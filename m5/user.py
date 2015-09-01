""" This module connects the user locally (to the database) and remotely (to the company website). """


from getpass import getpass
from requests import Session as RemoteSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from os.path import isdir, join
from os import mkdir
from logging import debug, info

from m5.settings import OUTPUT_DIR, LOGIN_URL, LOGOUT_URL, LOGGED_IN, REDIRECT, EXIT, FOLDER_NAMES, DATABASE_DIR
from m5.model import Model


class User:
    def __init__(self, username=None, password=None, offline=False, verbose=False):
        self.username = username
        self.password = password

        self.offline = offline
        self.verbose = verbose

        self.folders = {}

        self.sqlite_uri = None
        self.engine = None
        self.model = None
        self.db_session = None
        self.web_session = None

    def initialize(self):
        if not self.offline:
            self.web_session = RemoteSession()
            self._authenticate(self.username, self.password)

        self._check_install()
        self._connect_to_db()

    def _connect_to_db(self):
        self.db_uri = 'sqlite://' + DATABASE_DIR + '/sqlite.db'
        self.engine = create_engine(self.sqlite_uri, echo=self.verbose)
        self.model = Model.metadata.create_all(self.engine)
        self.db_session = sessionmaker(bind=self.engine)()

        debug('Switched on %s', self.db_uri)

    def _check_install(self):
        for folder_name in FOLDER_NAMES:
            folder_path = join(OUTPUT_DIR, self.username, folder_name)
            self.folders[folder_name] = folder_path

            if not isdir(folder_path):
                mkdir(folder_path)
                debug('Created folder: %s', folder_path)

    def _authenticate(self, username=None, password=None):
        if not username:
            self.username = input('Enter username: ')
        if not password:
            self.password = getpass('Enter password: ')

        credentials = {'username': self.username, 'password': self.password}
        response = self.web_session.post(LOGIN_URL, credentials)

        if LOGGED_IN not in response.text:
            self._authenticate(None, None)
        else:
            info('Logged into the remote server.')

    def logout(self):
        if not self.offline:
            response = self.web_session.get(LOGOUT_URL, params=EXIT)

            if response.history[0].status_code == REDIRECT:
                info('Logged out from the remote server.')
            self.web_session.close()

        exit(0)


if __name__ == '__main__':
    """ Test the module. """

    user = User(username='m5',
                password='PASSWORD',
                offline=False,
                verbose=True)

    user.initialize()
    user.logout()
