""" This module handles loading the local database into Pandas. """


from m5.settings import DEBUG, SKIP, LEAP
from pandas import DataFrame, read_sql
from pandas import merge
from collections import namedtuple


from m5.user import User

Database = namedtuple('Database', ['joined', 'orders', 'clients', 'checkins', 'checkouts'])


def load_table(user, table):
    """ Pull the database tables into Pandas and join them. """

    eng = user.engine

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

