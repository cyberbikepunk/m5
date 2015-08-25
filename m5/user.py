""" This module connects the user locally (to the database) and remotely (to the company website). """


from getpass import getpass
from requests import Session as RemoteSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from os.path import isdir
from os import mkdir

from m5.settings import USER_DIR, LOGIN_URL, LOGOUT_URL, STEP, LOGGED_IN, REDIRECT, EXIT
from m5.model import Model


class User:
    def __init__(self, username=None, password=None,
                 offline=False, verbose=False):

        self.username = username
        self.password = password

        self.offline = offline
        self.vernose = verbose

        self.user_dir = USER_DIR
        self.db_dir = USER_DIR + '/db'
        self.log_dir = USER_DIR + '/log'
        self.temp_dir = USER_DIR + '/temp'
        self.output_dir = USER_DIR + '/output'
        self.downloads_dir = USER_DIR + '/downloads'

        self.sqlite_uri = 'sqlite:///' + self.db_dir + '/' + username + '.sqlite'
        self.engine = None
        self.model = None

        self.local_session = None
        self.remote_session = None

    def initialize(self):
        if not self.offline:
            self.remote_session = RemoteSession()
            self._authenticate(self.username, self.password)

        self._check_install()
        self._connect_to_db()

    def _connect_to_db(self):
        self.engine = create_engine(self.sqlite_uri, echo=DEBUG)
        self.model = Model.metadata.create_all(self.engine)
        self.local_session = sessionmaker(bind=self.engine)()

    def _check_install(self):
        folders = (self.user_dir,
                   self.output_dir,
                   self.db_dir,
                   self.downloads_dir,
                   self.temp_dir,
                   self.log_dir)

        for folder in folders:
            if not isdir(folder):
                mkdir(folder)

        print('Created all user folders.')

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
