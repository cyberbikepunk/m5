""" User class and related stuff. """

from getpass import getpass
from requests import Session as RemoteSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from m5.settings import DEBUG, DATABASE, LOGIN, LOGOUT
from m5.utilities import log_me, safe_request
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

        # Say hello to the company server
        if not local:
            self.remote_session = RemoteSession()
            self._authenticate(username, password)

        # Create one database per user
        self.engine = create_engine('sqlite:///%s' % DATABASE, echo=DEBUG)
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

        credentials = {'username': self.username,
                       'password': self._password}

        # The server doesn't seem to care but...
        headers = {'user-agent': 'Mozilla/5.0'}
        self.remote_session.headers.update(headers)

        response = self.remote_session.post(LOGIN, credentials)
        if not response.ok:
            self._authenticate()
        else:
            print('Now logged into remote server.')

    def quit(self):
        """ Make a clean exit from the program. """
        self._logout()
        self.remote_session.close()
        exit(0)

    def _logout(self):
        """ Logout from the server and close the session. """
        response = self.remote_session.get(LOGOUT, params={'logout': '1'})
        if response.history[0].status_code == 302:
            # We have been redirected to the home page
            print('Logged out. Goodbye!')