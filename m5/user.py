""" This module connects the user locally (to the database) and remotely (to the company website). """
from glob import glob

from requests import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from os.path import isdir, join
from os import makedirs, remove
from logging import info
from shutil import rmtree, copytree


from m5.settings import USER_BASE_DIR, LOGIN_URL, LOGOUT_URL, LOGGED_IN, REDIRECT, EXIT, ASSETS_DIR, MOCK_DIRNAME
from m5.model import Model


class UserError(Exception):
    pass


def initialize(user=None, **kwargs):
    user = user or User(**kwargs)

    try:
        if user.offline:
            user.check_installation()
        else:
            user.authenticate()
            user.soft_install()
    except UserError:
        raise

    user.start_db()

    return user


class User:
    def __init__(self,
                 username=None,
                 password=None,
                 offline=False,
                 verbose=False):

        self.username = username
        self.password = password

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
        self.engine = create_engine(self.db_uri, echo=self.verbose)
        self.model = Model.metadata.create_all(self.engine)
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
        self.mock_dir = join(ASSETS_DIR, MOCK_DIRNAME)

    def clear(self):
        try:
            rmtree(self.userdir)
        except FileNotFoundError:
            pass
        return self

    def flush(self):
        for file in glob(join(self.archive, '*.html')):
            remove(file)
        return self

    def bootstrap(self):
        try:
            copytree(self.mock_dir, self.userdir)
        except FileExistsError:
            pass
        return self

