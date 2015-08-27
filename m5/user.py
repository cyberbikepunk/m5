""" This module connects the user locally (to the database) and remotely (to the company website). """


from getpass import getpass
from requests import Session as RemoteSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from os.path import isdir, join
from os import mkdir
from logging import debug

from m5.settings import ROOT_DIR, LOGIN_URL, LOGOUT_URL, STEP, LOGGED_IN, REDIRECT, EXIT, FOLDER_NAMES
from m5.model import Model


class User:
    def __init__(self, username=None, password=None, offline=False, verbose=False):
        self.username = username
        self.password = password
        self.offline = offline
        self.verbose = verbose
        self.folders = {}
        self.sqlite_uri = ''
        self.engine = None
        self.model = None
        self.local_session = None
        self.remote_session = None

    def initialize(self):
        self._check_install()
        self._connect_to_db()
        if not self.offline:
            self.remote_session = RemoteSession()
            self._authenticate(self.username, self.password)

    def _connect_to_db(self):
        self.db = 'sqlite:///' + self.folders['db'] + '/' + self.username + '.db'
        self.engine = create_engine(self.sqlite_uri, echo=self.verbose)
        self.model = Model.metadata.create_all(self.engine)
        self.local_session = sessionmaker(bind=self.engine)()
        debug('Switched on database: %s', self.db)

    def _check_install(self):
        for folder_name in FOLDER_NAMES:
            folder_path = join(ROOT_DIR, self.username, folder_name)
            self.folders[folder_name] = folder_path
            if not isdir(folder_path):
                mkdir(folder_path)
                debug('Created folder: %s', folder_path)

    def _authenticate(self, username=None, password=None):
        """ Make recursive login attempts to the website. """

        if not username:
            self.username = input('Enter username: ')
        if not password:
            self.password = getpass('Enter password: ')

        response = self.remote_session.post(LOGIN_URL,
                                            {'username': self.username,
                                             'password': self.password})

        if LOGGED_IN not in response.text:
            print('Wrong credentials.', end=STEP)
            self._authenticate(None, None)
        else:
            print('Logged into the remote server.')

    def logout(self):
        if not self.offline:
            response = self.remote_session.get(LOGOUT_URL, params=EXIT)

            if response.history[0].status_code == REDIRECT:
                print('Logged out from the remote server.')
            self.remote_session.close()

        exit(0)


if __name__ == '__main__':
    user = User()

    user.initialize()
    user.logout()
