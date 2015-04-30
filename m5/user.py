""" Connect the user to the local and remote databases. """

from collections import namedtuple
from getpass import getpass
from glob import iglob
from pandas import DataFrame, read_sql
from requests import Session as RemoteSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from os.path import join, isdir, getctime
from pandas import merge
from os import mkdir, chmod, listdir
from numpy import int64

from settings import DEBUG, LOGIN_URL, LOGOUT_URL, DATABASE_DIR, STEP, USER_DIR, OUTPUT_DIR
from settings import TEMP_DIR, LOG_DIR, DOWNLOADS, OFFLINE, LEAP, SKIP
from model import Model

Database = namedtuple('Database', ['joined', 'orders', 'clients', 'checkins', 'checkouts'])


class User:
    """ Users work for Messenger (http://messenger.de). """

    def __init__(self, username=None, password=None, db_file=None):
        """ Authenticate the user and load data from the local database. """

        self.username = username
        self.password = password

        if not OFFLINE:
            self.remote_session = RemoteSession()
            self._authenticate(username, password)
        else:
            self.remote_session = None

        self._check_install()

        self.db_file = db_file if db_file else self._latest_db
        path = join(DATABASE_DIR, self.db_file)
        sqlite = 'sqlite:///{db}'.format(db=path)

        self.engine = create_engine(sqlite, echo=DEBUG)
        self.model = Model.metadata.create_all(self.engine)
        self.local_session = sessionmaker(bind=self.engine)()

        self.db = None
        self._load_db()

    @staticmethod
    def _check_install():
        """ Create user folders as needed. """

        folders = (USER_DIR, OUTPUT_DIR, DATABASE_DIR, DOWNLOADS, TEMP_DIR, LOG_DIR)

        for folder in folders:
            if not isdir(folder):
                # Setting permissions directly with mkdir gives me bizarre results. Why?
                mkdir(folder)
                chmod(folder, 0o755)
                print('Created %s' % folder)

    @property
    def _latest_db(self):
        """ Return the most recent database. """

        if listdir(DATABASE_DIR):
            filepath = max(iglob(join(DATABASE_DIR, '*.sqlite')), key=getctime)
        else:
            filepath = '%s.sqlite' % self.username

        print('Selected %s' % filepath)
        return filepath

    def _load_db(self) -> DataFrame:
        """ Pull the database tables into Pandas and join them. """

        eng = self.engine

        clients = read_sql('client', eng, index_col='client_id')
        orders = read_sql('order', eng, index_col='order_id', parse_dates=['date'])
        checkins = read_sql('checkin', eng, index_col='timestamp', parse_dates=['timestamp', 'after_', 'until'])
        checkpoints = read_sql('checkpoint', eng, index_col='checkpoint_id')
        checkpoints = self._typecast_checkpoint_ids(checkpoints)

        checkins_with_checkpoints = merge(left=checkins,
                                          right=checkpoints,
                                          left_on='checkpoint_id',
                                          right_index=True,
                                          how='left')

        orders_with_clients = merge(left=orders,
                                    right=clients,
                                    left_on='client_id',
                                    right_index=True,
                                    how='left')

        joined = merge(left=checkins_with_checkpoints,
                       right=orders_with_clients,
                       left_on='order_id',
                       right_index=True,
                       how='left')

        joined.sort_index(inplace=True)
        clients.sort_index(inplace=True)
        orders.sort_index(inplace=True)
        checkins.sort_index(inplace=True)
        checkpoints.sort_index(inplace=True)

        self.db = Database(joined, orders, clients, checkins, checkpoints)
        print('Loaded the database into Pandas.', end=LEAP)

        if DEBUG:
            print('ORDERS:', end=SKIP)
            print(orders.info(), end=LEAP)
            print('CLIENTS:', end=SKIP)
            print(clients.info(), end=LEAP)
            print('CHECKINS:', end=SKIP)
            print(checkins.info(), end=LEAP)
            print('CHECKPOINTS:', end=SKIP)
            print(checkpoints.info(), end=LEAP)
            print('JOINED:', end=SKIP)
            print(joined.info(), end=SKIP)

    def _authenticate(self, username=None, password=None):
        """ Make recursive login attempts. """

        self.username = username if username else input('Enter username: ')
        self.password = password if password else getpass('Enter password: ')

        # The server doesn't seem to care anyways.
        headers = {'user-agent': 'Mozilla/5.0'}
        self.remote_session.headers.update(headers)

        url = LOGIN_URL
        credentials = {'username': self.username, 'password': self.password}
        response = self.remote_session.post(url, credentials)

        # Login failure gives me a 200 response.
        if 'erfolgreich' not in response.text:
            print('Wrong credentials. Try again.', end=STEP)
            self._authenticate(None, None)
        else:
            print('Logged into the remote server.')

    @staticmethod
    def _typecast_checkpoint_ids(checkpoints):
        # This bug has been fixed but we keep this for older versions of the database.
        if checkpoints.index.dtype != 'int64':
            checkpoints.reset_index(inplace=True)
            checkpoint_ids = checkpoints['checkpoint_id'].astype(int64, raise_on_error=True)
            checkpoints['checkpoint_id'] = checkpoint_ids
            checkpoints.set_index('checkpoint_id', inplace=True)
        return checkpoints

    def quit(self):
        """ Make a clean exit. """

        if not OFFLINE:
            url = LOGOUT_URL
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