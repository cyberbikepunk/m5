""" This module connects the user locally (to the database) and remotely (to the company website). """


from requests import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from os.path import isdir, join
from os import mkdir
from logging import debug, info

from m5.settings import OUTPUT_DIR, LOGIN_URL, LOGOUT_URL, LOGGED_IN, REDIRECT, EXIT, DATABASE_DIR
from m5.model import Model


class UserError(Exception):
    pass


def initialize(**kwargs):
    user = User(**kwargs)
    user.authenticate()
    user.start_db()
    return user


class User:
    def __init__(self, username=None, password=None, offline=False, verbose=False):
        self.username = username
        self.password = password

        self.offline = offline
        self.verbose = verbose

        self.downloads = join(OUTPUT_DIR, username, 'downloads')
        self.output = join(OUTPUT_DIR, username, 'output')

        self.sqlite_uri = None
        self.engine = None
        self.model = None

        self.db_session = None
        self.web_session = None

    def authenticate(self):
        if self.offline:
            self._local_authenticate()
        else:
            self.web_session = Session()
            self._remote_authenticate()
            self._check_install()

    def start_db(self):
        self.sqlite_uri = 'sqlite://' + DATABASE_DIR + '/sqlite.db'
        self.engine = create_engine(self.sqlite_uri, echo=self.verbose)
        self.model = Model.metadata.create_all(self.engine)
        self.db_session = sessionmaker(bind=self.engine)()

        debug('Switched on %s', self.sqlite_uri)

    def _check_install(self):
        mkdir(self.downloads)
        mkdir(self.output)
        debug('Created user folders')

    def _local_authenticate(self):
        return isdir(self.downloads) and isdir(self.output)

    def _login(self):
        credentials = {'username': self.username, 'password': self.password}
        return self.web_session.post(LOGIN_URL, credentials)

    def _remote_authenticate(self):
        response = self._login()
        if LOGGED_IN in response.text:
            info('Remote authenticated')
        else:
            raise UserError('Bad credentials')

    def quit(self):
        if not self.offline:
            response = self.web_session.get(LOGOUT_URL, params=EXIT)
            if response.history[0].status_code == REDIRECT:
                self.web_session.close()

        info('Goodbye!')
        exit(0)
