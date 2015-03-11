"""  Check the consistency and quality of the data. """

from math import ceil

from m5.settings import LEAP, POP, OUTPUT
from m5.user import User
from m5.utilities import unique_file, print_header

import matplotlib.pyplot as plt
import pandas as pd


class Quality():
    """
    The quality of the data depends on how well the scraper performed.
    Quality helps to quantify and visualize the overall data quality.
    """

    def __init__(self, db: pd.DataFrame):
        self.db = db

    def check_sums(self):
        """ Count the number of empty cells (distinguish NaN, None and 0). """

        # I'm creating an empty data-frame and filling each
        # cell on by one. This is definitely not the Pandas
        # way to do it, especially when counting NaN instances.

        reports = dict()
        count = dict()

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

        for name, table in self.db.items():
            # Start by producing an empty report
            # table for each table in the database.
            columns = list(table.columns.values)
            reports[name] = pd.DataFrame(None, index=index, columns=columns)

            for column in columns:
                # In each column, we now look
                # for occurrences of 0 and NaN.
                series = self.db[name][column]

                conditions = [('True', (series.apply(lambda x: bool(x)))),
                              ('Zero', (series == 0)),
                              ('NaN', (series.isnull())),
                              ('None', (series.apply(lambda x: True if x is None else False)))]

                for (row, condition) in conditions:
                    total = series[condition].size

                    count['total'] = total
                    count['%'] = total / series.size * 100

                    # Store the results in the right place inside the report table.
                    reports[name].loc[(row, 'total'), column] = count['total']
                    reports[name].loc[(row, '%'), column] = ceil(count['%'])

            # Check-sum using the NaN and None counts separately
            nans = reports[name].xs('%', level='count').drop('None').T
            nones = reports[name].xs('%', level='count').drop('NaN').T

            nans['Sum'] = nans.sum(axis=1)
            nones['Sum'] = nones.sum(axis=1)

            # Print the report
            print_header(name)
            print(reports[name], end=LEAP)

            print('Sum with NaNs = ', end=LEAP)
            print(nans, end=LEAP)
            print('Sum with Nones = ', end=LEAP)
            print(nones, end=LEAP)

            if POP:
                nones.plot(kind='bar', stacked=True, subplots=True, layout=(2, 2), figsize=(12, 12), sharex=False)
                nans.plot(kind='bar', stacked=True, subplots=True, layout=(2, 2), figsize=(12, 12), sharex=False)

            plt.savefig(unique_file(OUTPUT, name + '-nones.png'))
            plt.savefig(unique_file(OUTPUT, name + '-nans.png'))

        pd.reset_option('precision')

    def summarize_db(self):
        """ Print out the most basic information about the database. """

        # Table size information
        print_header('Table sizes')

        for name, table in self.db.items():
            print('{table}: {shape}'.format(table=name, shape=table.shape), end=LEAP)

        # Table summary information
        print_header('Table infos')

        for name, table in self.db.items():
            print('Table %s = ' % name, end=LEAP)
            print(table.info(), end=LEAP)

    def check_keys(self):
        """
        Explore the results of different types of table SQL-type
        join operations: left, right, inner, outer joins.
        """

        # Play with a copy
        db = self.db.copy()

        for name, table in db.items():
            table.reset_index(inplace=True)

        methods = ('left', 'right', 'inner', 'outer')

        for method in methods:
            joined = pd.merge(left=db['checkins'],
                              right=db['checkpoints'],
                              left_on='checkpoint_id',
                              right_on='checkpoint_id',
                              how=method)
            joined.reset_index(inplace=True)

            print_header(method)
            print(joined.info())


if __name__ == '__main__':

    user = User()
    q = Quality(user.db)

    q.summarize_db()
    q.check_sums()
    q.check_keys()
