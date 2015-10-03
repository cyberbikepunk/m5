""" This module connects the user locally (to the database) and remotely (to the company website). """


from glob import glob
from itertools import chain
from requests import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from os.path import isdir, join
from os import makedirs, remove
from logging import info
from shutil import rmtree, copytree


from m5.settings import LOGGED_IN, REDIRECT, EXIT, ASSETS_DIR, MOCK_DIRNAME
from m5.settings import USER_BASE_DIR, LOGIN_URL, LOGOUT_URL, USERNAME, PASSWORD
from m5.model import Model


class UserError(Exception):
    pass


class User:
    def __init__(self,
                 username=None,
                 password=None,
                 offline=False,
                 verbose=False):

        self.username = username or USERNAME
        self.password = password or PASSWORD

        self.userdir = ''
        self.archive = ''
        self.plots = ''

        self.offline = offline
        self.verbose = verbose

        self.db_uri = None
        self.engine = None
        self.model = None

        self.db = None
        self.web = Session()

        if username:
            self._configure(username)

    def init(self):
        try:
            if self.offline:
                self.check_installation()
            else:
                self.authenticate()
                self.soft_install()
        except UserError:
            raise

        self.start_db()

        info('User initialization done')
        return self

    def _configure(self, dirname):
        self.userdir = join(USER_BASE_DIR, dirname)
        self.archive = join(USER_BASE_DIR, dirname, 'archive')
        self.plots = join(USER_BASE_DIR, dirname, 'plots')

        self.db_uri = 'sqlite:///' + self.userdir + '/' + dirname + '.sqlite'

    def check_installation(self):
        if self.offline:
            if not all(list(map(isdir, self.folders))):
                raise UserError('Missing directories')

        info('User is returning')

    def authenticate(self):
        response = self._login()
        if LOGGED_IN not in response.text:
            raise UserError('Authentication failed')

        info('User authenticated')

    def start_db(self):
        self.engine = create_engine(self.db_uri)
        Model.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()

        info('Switched on database')

    @property
    def folders(self):
        return [self.archive,
                self.plots,
                self.userdir]

    def soft_install(self):
        for folder in self.folders:
            if not isdir(folder):
                makedirs(folder)

        info('Created user folders')

    def _login(self):
        return self.web.post(LOGIN_URL, data={'username': self.username, 'password': self.password})

    def logout(self):
        if not self.offline:
            response = self.web.get(LOGOUT_URL, params=EXIT)
            if response.history[0].status_code == REDIRECT:
                self.web.close()

        info('Goodbye')

    def __str__(self):
        return self.username


class Ghost(User):
    def __init__(self, **kwargs):
        super(Ghost, self).__init__(**kwargs)
        self._configure(MOCK_DIRNAME)

    def clear(self):
        try:
            rmtree(self.userdir)
        except FileNotFoundError:
            pass
        return self

    def flush(self):
        files = [join(self.archive, '*.html'),
                 join(self.plots, '*.png'),
                 join(self.userdir, '*.sqlite')]

        for file in chain(*list(map(glob, files))):
            remove(file)
        return self

    def bootstrap(self):
        try:
            copytree(join(ASSETS_DIR, MOCK_DIRNAME), self.userdir)
        except FileExistsError:
            pass
        return self

