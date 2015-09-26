""" This module connects the user locally (to the database) and remotely (to the company website). """


from requests import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from os.path import isdir, join
from os import makedirs
from logging import info

from m5.settings import OUTPUT_DIR, LOGIN_URL, LOGOUT_URL, LOGGED_IN, REDIRECT, EXIT
from m5.model import Model


class UserException(Exception):
    pass


def initialize(**kwargs):
    user = User(**kwargs)
    user.authenticate()
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

        self.offline = offline
        self.verbose = verbose

        self.user_dir = join(OUTPUT_DIR, username)
        self.download_dir = join(OUTPUT_DIR, username, 'downloads')
        self.output_dir = join(OUTPUT_DIR, username, 'output')

        self.db_uri = None
        self.engine = None
        self.model = None

        self.db_session = None
        self.web_session = Session()

    def authenticate(self):
        if self.offline:
            if not all(self._folders):
                raise UserException('Missing directories')
        else:
            if LOGGED_IN in self._login().text:
                self._install()
            else:
                raise UserException('Authentication failed')

        info('User authenticated')

    def start_db(self):
        self.db_uri = 'sqlite:///' + self.user_dir + '/database.sqlite'
        self.engine = create_engine(self.db_uri, echo=self.verbose)
        self.model = Model.metadata.create_all(self.engine)
        self.db_session = sessionmaker(bind=self.engine)()

        info('Switched on database')

    @property
    def _folders(self):
        return [self.download_dir,
                self.output_dir,
                self.user_dir]

    def _install(self):
        for folder in self._folders:
            if not isdir(folder):
                makedirs(folder)

        info('Created user folders')

    def _login(self):
        return self.web_session.post(LOGIN_URL, data={'username': self.username,
                                                      'password': self.password})

    def quit(self):
        if not self.offline:
            response = self.web_session.get(LOGOUT_URL, params=EXIT)
            if response.history[0].status_code == REDIRECT:
                self.web_session.close()

        info('Goodbye!')

    def __str__(self):
        return self.username
