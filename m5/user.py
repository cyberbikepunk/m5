""" Connect the user to the local and remote databases. """

from getpass import getpass
from pandas import DataFrame, read_sql
from requests import Session as RemoteSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from os.path import join, isfile, isdir
from pandas import merge
from os import mkdir, chmod

from m5.settings import DEBUG, LOGIN, LOGOUT, DATABASE, STEP, LEAP, USER, OUTPUT, TEMP, LOG, DOWNLOADS, OFFLINE
from m5.utilities import log_me, latest_file, fix_checkpoints, print_header
from m5.model import Base


class User:
    """ Users must work for Messenger (http://messenger.de). """

    def __init__(self, username=None, password=None, db_file=None):
        """ Authenticate the user and start a local database session. """

        # Awaiting authentication.
        self.username = username
        self.password = password

        if not OFFLINE:
            # Verify the user on the remote server.
            self.remote_session = RemoteSession()
            self._authenticate(username, password)
        else:
            # Most of the modules can be run in offline mode.
            # Turn it off to download more data from the server.
            self.remote_session = None

        # Create folders if needed.
        self._check_install()

        # Use specified database or select the latest.
        db_file = latest_file(DATABASE) if not db_file else db_file
        path = join(DATABASE, db_file)
        sqlite = 'sqlite:///{db}'.format(db=path)

        # Build the model and switch on the database.
        self.engine = create_engine(sqlite, echo=DEBUG)
        self.base = Base.metadata.create_all(self.engine)
        self.local_session = sessionmaker(bind=self.engine)()

        # Pull data into memory
        self.db = self._load()

    @staticmethod
    def _check_install():
        """ Create user folders as needed. """

        folders = (USER, OUTPUT, DATABASE, DOWNLOADS, TEMP, LOG)

        for folder in folders:
            if not isdir(folder):
                mkdir(folder)
                # Setting permissions directly with
                # mkdir gives me bizarre results.
                chmod(folder, 0o755)
                print('Created %s' % folder)

    @log_me
    def _load(self) -> DataFrame:
        """ Pull the database tables into Pandas and join them together. """

        db = dict()
        eng = self.engine

        db['clients'] = read_sql('client', eng, index_col='client_id')
        db['orders'] = read_sql('order', eng, index_col='order_id', parse_dates=['date'])
        db['checkins'] = read_sql('checkin', eng, index_col='checkin_id', parse_dates=['timestamp', 'after_', 'until'])
        db['checkpoints'] = read_sql('checkpoint', eng, index_col='checkpoint_id')

        # Make sure the primary key of the checkpoint table
        # is an integer. This bug has now been fixed but we
        # keep this here for compatibility with old databases.
        db['checkpoints'] = fix_checkpoints(db['checkpoints'])

        checkins_with_checkpoints = merge(left=db['checkins'],
                                          right=db['checkpoints'],
                                          left_on='checkpoint_id',
                                          right_index=True,
                                          how='left')

        orders_with_clients = merge(left=db['orders'],
                                    right=db['clients'],
                                    left_on='client_id',
                                    right_index=True,
                                    how='left')

        db['all'] = merge(left=checkins_with_checkpoints,
                          right=orders_with_clients,
                          left_on='order_id',
                          right_index=True,
                          how='left')

        if DEBUG:
            print_header('User data summary')
            for title, table in db.items():
                print('Pandas DataFrame (%s):' % title)
                print(table.reset_index().info(), end=LEAP)

        return db

    @log_me
    def _authenticate(self, username=None, password=None):
        """ Make recursive login attempts. """

        self.username = username if username else input('Enter username: ')
        self.password = password if password else getpass('Enter password: ')

        # The server doesn't seem to care but...
        headers = {'user-agent': 'Mozilla/5.0'}
        self.remote_session.headers.update(headers)

        url = LOGIN
        credentials = {'username': self.username, 'password': self.password}
        response = self.remote_session.post(url, credentials)

        if 'erfolgreich' not in response.text:
            print('Wrong credentials. Try again.', end=STEP)
            self._authenticate(None, None)
        else:
            print('Logged into the remote server.')

    def quit(self):
        """ Make a clean exit. """

        if not OFFLINE:

            url = LOGOUT
            payload = {'logout': '1'}
            response = self.remote_session.get(url, params=payload)

            if response.history[0].status_code == 302:
                # We've been redirected to the login page:
                # either we've successfully logged out or
                # our request session had timed-out anyways.
                print('Logged out. Goodbye!')
            self.remote_session.close()

        exit(0)


if __name__ == '__main__':
    user = User()
    user.quit()