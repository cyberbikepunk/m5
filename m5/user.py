""" Connect the user to the local and remote databases. """

from getpass import getpass
from pandas import DataFrame, read_sql
from requests import Session as RemoteSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from os.path import join
from pandas import merge, set_option

from m5.settings import DEBUG, LOGIN, LOGOUT, DATABASE, SKIP, REMOTE
from m5.utilities import check_install, log_me, latest_file
from m5.model import Base


class User:
    """ Users must work for Messenger (http://messenger.de). """

    def __init__(self, username: str, password: str):
        """ Authenticate the user on the remote server and start a local database session. """

        self.username = username
        self._password = password

        if REMOTE:
            # Say hello to the remote server.
            self.remote_session = RemoteSession()
            self._authenticate(username, password)
        else:
            print('Ignore the remote server.')

        # Create folders for new user.
        check_install()

        # Use the most recent database in the folder
        path = join(DATABASE, latest_file(DATABASE))
        sqlite = 'sqlite:///{path}'.format(path=path)
        print('The latest database is {path}'.format(path=path))

        # Start a new local database session.
        self.engine = create_engine(sqlite, echo=DEBUG)
        self.base = Base.metadata.create_all(self.engine)
        self.local_session = sessionmaker(bind=self.engine)()

        # Pull data into memory
        self.db = self._load()

    @log_me
    def _load(self) -> DataFrame:
        """ Pull the database tables into Pandas and join them together. """

        db = dict()
        eng = self.engine

        db['clients'] = read_sql('client', eng, index_col='client_id')
        db['orders'] = read_sql('order', eng, index_col='order_id', parse_dates=['date'])
        db['checkins'] = read_sql('checkin', eng, index_col='checkin_id', parse_dates=['timestamp', 'after_', 'until'])
        db['checkpoints'] = read_sql('checkpoint', eng, index_col='checkpoint_id')

        checkins_with_checkpoints = merge(left=db['checkins'],
                                          right=db['checkpoints'],
                                          left_on='checkpoint_id',
                                          right_index=True,
                                          how='outer')

        orders_with_clients = merge(db['orders'],
                                    db['clients'],
                                    left_on='client_id',
                                    right_index=True,
                                    how='outer')

        db['all'] = merge(checkins_with_checkpoints,
                          orders_with_clients,
                          left_on='order_id',
                          right_index=True,
                          how='outer')

        if DEBUG:
            for table in db.values():
                print(table.info(), end=SKIP)

        return db

    @log_me
    def _authenticate(self, username=None, password=None):
        """ Make recursive login attempts. """

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
        """ Make a clean exit. """

        if REMOTE:
            response = self.remote_session.get(LOGOUT, params={'logout': '1'})
            if response.history[0].status_code == 302:
                # We know we are logged out because we
                # have been redirected to the login page
                print('Logged out. Goodbye!')
            self.remote_session.close()

        exit(0)


if __name__ == '__main__':
    user = User('x', 'y')
    user.quit()