""" User class and related stuff. """

from os.path import dirname, join
from getpass import getpass
from requests import Session as RequestsSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from m5.utilities import notify, log_me, safe_request, DEBUG
from m5.model import Base


class User:
    """
    The User class manages user activity for couriers freelancing
    for User (http://messenger.de). This is the default user class.
    It can theoretically be overridden for other courier companies.
    """

    def __init__(self, username: str=None, password: str=None, local=False):
        """  Authenticate the user on the remote server and initialise the local database. """

        self.username = username
        self._password = password
        self.local = local

        # Say hello to the company server
        if not local:
            self.remote_session = RequestsSession()
            self._authenticate(self.username, self._password)

        # Make paths bulletproof
        self.m5_path = dirname(__file__)
        self.db_path = join(self.m5_path, '../db/%s.sqlite' % self.username)
        self.downloads = join(self.m5_path, '../downloads', username)

        # Create one database per user
        self.engine = create_engine('sqlite:///%s' % self.db_path, echo=DEBUG)
        self.Base = Base.metadata.create_all(self.engine)

        # Start a database query session
        _Session = sessionmaker(bind=self.engine)
        self.database_session = _Session()

    @log_me
    @safe_request
    def _authenticate(self, username=None, password=None):
        """ Make recursive login attempts until successful. """

        if not username:
            self.username = input('Enter username: ')
        if not password:
            self._password = getpass('Enter password: ')

        url = 'http://bamboo-mec.de/ll.php5'
        credentials = {'username': self.username,
                       'password': self._password}

        # The server doesn't seem to care but...
        headers = {'user-agent': 'Mozilla/5.0'}
        self.remote_session.headers.update(headers)

        response = self.remote_session.post(url, credentials)
        if not response.ok:
            self._authenticate()
        else:
            print('Now logged into remote server.')

    def quit(self):
        """ Make a clean exit from the program. """

        self._logout()
        exit(0)

    def _logout(self):
        """ Logout from the server and close the session. """

        url = 'http://bamboo-mec.de/index.php5'
        payload = {'logout': '1'}

        response = self.remote_session.get(url, params=payload)

        if response.history[0].status_code == 302:
            # We have been redirected to the home page
            notify('Logged out. Goodbye!')

        self.remote_session.close()
