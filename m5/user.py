""" This module connects the user locally (to the database) and remotely (to the company website). """


from requests import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from os.path import isdir, join
from os import makedirs
from logging import info

from m5.settings import OUTPUT_DIR, LOGIN_URL, LOGOUT_URL, LOGGED_IN, REDIRECT, EXIT, DATABASE_DIR
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

        self.downloads = join(OUTPUT_DIR, username, 'downloads')
        self.output = join(OUTPUT_DIR, username, 'output')
        self.log = join(OUTPUT_DIR, 'log')

        self.sqlite_uri = None
        self.engine = None
        self.model = None

        self.db_session = None
        self.web_session = Session()

    def authenticate(self):
        if self.offline:
            self._check_directories()

        else:
            response = self._post_credentials()

            if LOGGED_IN in response.text:
                self._make_directories()
            else:
                raise UserException('User authentication failed')

            info('Remote authenticated')

    def start_db(self):
        self.sqlite_uri = 'sqlite://' + DATABASE_DIR + '/sqlite.db'
        self.engine = create_engine(self.sqlite_uri, echo=self.verbose)
        self.model = Model.metadata.create_all(self.engine)
        self.db_session = sessionmaker(bind=self.engine)()

        info('Switched on database')

    def _check_directories(self):
        if not isdir(self.downloads) or not isdir(self.output):
            raise UserException('No existing directories')

    def _make_directories(self):
        if not isdir(self.log):
            makedirs(self.log)
        if not isdir(self.downloads):
            makedirs(self.downloads)
        if not isdir(self.output):
            makedirs(self.output)

        info('Created user folders')

    def _post_credentials(self):
        return self.web_session.post(LOGIN_URL, data={'username': self.username,
                                                      'password': self.password})

    def quit(self):
        if not self.offline:
            response = self.web_session.get(LOGOUT_URL, params=EXIT)

            if response.history[0].status_code == REDIRECT:
                self.web_session.close()

        info('Goodbye!')

    def __repr__(self):
        return '<User: %s' + self.username + '>'

    def __str__(self):
        return self.username


if __name__ == '__main__':
    u = User(username='m-134', password='PASSWORD', offline=True)
    u.authenticate()
