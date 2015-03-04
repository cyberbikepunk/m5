"""  The module that produces statistics, maps and plots. """

from m5.settings import DEBUG, FILL_1, FILL_2, SKIP, CENTER
from m5.utilities import force_unique

from sqlalchemy.engine import Engine
from sqlalchemy.orm.session import Session
from math import ceil

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


class Stats():

    def __init__(self, session: Session, engine: Engine):
        """ Instantiate an empty object. """

        self.session = session
        self.engine = engine

        self.df = dict()

        self.orders = None
        self.clients = None
        self.checkins = None
        self.checkpoints = None

    def fetch_data(self):
        """ Pull the database tables into Pandas. """

        self.clients = pd.read_sql_table('client', self.engine, index_col='client_id')
        self.orders = pd.read_sql('order', self.engine, index_col='order_id', parse_dates=['date'])
        self.checkins = pd.read_sql('checkin', self.engine, index_col='checkin_id', parse_dates=['timestamp', 'after_', 'until'])
        self.checkpoints = pd.read_sql('checkpoint', self.engine, index_col='checkpoint_id')

        self.df['clients'] = self.clients
        self.df['orders'] = self.orders
        self.df['checkins'] = self.checkins
        self.df['checkpoints'] = self.checkpoints

        if DEBUG:
            pd.set_option('expand_frame_repr', False)
            print(self.clients)
            print(self.orders.tail(3500))
            print(self.checkins)
            print(self.checkpoints)

    def check_data(self):
        """ Count the number of empty cells (distinguish NaN and 0). """

        # I'm creating an empty data-frame and filling each
        # cell on by one. This is definitely not the Pandas
        # way to do it, especially when counting NaN instances.

        reports = dict()
        count = dict()

        print(SKIP)
        print('{title:{fill}{align}100}'.format(title='Data check', fill=FILL_1, align=CENTER, end=SKIP))
        pd.set_option('precision', 3)
        pd.set_option('display.mpl_style', 'default')

        indices = [('True', 'total'),
                   ('True', '%'),
                   ('Zero', 'total'),
                   ('Zero', '%'),
                   ('NaN', 'total'),
                   ('NaN', '%'),
                   ('None', 'total'),
                   ('None', '%')]

        index = pd.MultiIndex.from_tuples(indices, names=['type', 'count'])

        for table_name, table in self.df.items():
            # Start by producing an empty report
            # table for each table in the database.
            columns = list(table.columns.values)
            reports[table_name] = pd.DataFrame(None, index=index, columns=columns)

            for column in columns:
                # In each column, we now look
                # for occurrences of 0 and NaN.
                series = self.df[table_name][column]

                conditions = [('True', (series.apply(lambda x: bool(x)))),
                              ('Zero', (series == 0)),
                              ('NaN', (series.isnull())),
                              ('None', (series.apply(lambda x: True if x is None else False)))]

                for (row, condition) in conditions:
                    total = series[condition].size

                    count['total'] = total
                    count['%'] = total / series.size * 100

                    # Store the results in the right place inside the report table.
                    reports[table_name].loc[(row, 'total'), column] = count['total']
                    reports[table_name].loc[(row, '%'), column] = ceil(count['%'])

            # Check-sum using the NaN and None counts separately
            nans = reports[table_name].xs('%', level='count').drop('None').T
            nones = reports[table_name].xs('%', level='count').drop('NaN').T

            nans['Sum'] = nans.sum(axis=1)
            nones['Sum'] = nones.sum(axis=1)

            # Print the report
            print('{title:{fill}{align}100}'.format(title=table_name, fill=FILL_2, align=CENTER))
            print(reports[table_name], end=SKIP)

            print('Sum with NaN:')
            print(nans, end=SKIP)
            print('Sum with Nones:')
            print(nones, end=SKIP)

            nones.plot(kind='bar', stacked=True, subplots=True, layout=(2, 2), figsize=(6, 6), sharex=False)
            plt.savefig(force_unique(table_name + '-nans' + '.png'))
            nans.plot(kind='bar', stacked=True, subplots=True, layout=(2, 2), figsize=(6, 6), sharex=False)
            plt.savefig(force_unique(table_name + '-nones' + '.png'))

        pd.reset_option('precision')

    def show_data(self):
        """
        The quality of the data scraped from the website is crucial.
        This method gives a quick overview of what the data looks like.
        """

        print(SKIP)

        # Table sizes
        # -----------------------------------------------------------------------------------------------------
        print('{title:{fill}{align}100}'.format(title='Table sizes', fill=FILL_1, align=CENTER), end=SKIP)

        print('Clients table: {shape}'.format(shape=self.clients.shape))
        print('Orders table: {shape}'.format(shape=self.orders.shape))
        print('Checkins table : {shape}'.format(shape=self.checkins.shape))
        print('Checkpoints table: {shape}'.format(shape=self.checkpoints.shape), end=SKIP)

        # Table information
        # -----------------------------------------------------------------------------------------------------
        print('{title:{fill}{align}100}'.format(title='Table infos', fill=FILL_1, align=CENTER), end=SKIP)

        print('{title:{fill}{align}50}'.format(title='CLIENTS', fill=FILL_2, align=CENTER))
        print(self.clients.info(), end=SKIP)

        print('{title:{fill}{align}50}'.format(title='ORDERS', fill=FILL_2, align=CENTER))
        print(self.orders.info(), end=SKIP)

        print('{title:{fill}{align}50}'.format(title='CHECKINS', fill=FILL_2, align=CENTER))
        print(self.checkins.info(), end=SKIP)

        print('{title:{fill}{align}50}'.format(title='CHECKPOINTS', fill=FILL_2, align=CENTER))
        print(self.checkpoints.info(), end=SKIP)




