"""  Check the quality and consistency of the database. """

from numbers import Number
from m5.settings import LEAP, DEBUG
from m5.user import User
from m5.utilities import print_header, Visualizor
from pandas import DataFrame, isnull, merge
from numpy import nan


class Inspector(Visualizor):
    """ Visualize quality and consitency of the data. """

    def __init__(self, db: DataFrame):
        super(Inspector, self).__init__(db)

    def empty_cells(self):
        """ Count False, 0, None and Null values in the data. """

        fig = self.prepare_image('Empty cells')
        indexes = [221, 222, 223, 224]

        titles = ['Boolean False',
                  'Number 0',
                  'Pandas Null',
                  'NoneType']

        masks = [lambda x: not bool(x),
                 lambda x: issubclass(x.__class__, Number) and x == 0,
                 lambda x: isnull(x),
                 lambda x: x is None]

        for index, title, mask in zip(indexes, titles, masks):
            masked = self.db['all'].applymap(mask).applymap(int).sum()

            if DEBUG:
                print_header(title)
                print(masked, end=LEAP)

            masked.plot(kind='bar',
                        sharey=True,
                        sharex=True,
                        ylim=(0, self.db['all'].shape[0]),
                        axes=fig.add_subplot(index, title=title))

        self.make_image('masked_db.png')

    def db_info(self):
        """ Print out basic information about the data. """

        print_header('Table sizes')
        for name, table in self.db.items():
            print('{table}: {shape}'.format(table=name, shape=table.shape))

        print_header('Table infos')
        for name, table in self.db.items():
            print('Table %s = ' % name, end=LEAP)
            print(table.info(), end=LEAP)

    def table_joins(self):
        """ Test left, right, inner & outer joins on adjacent tables. """

        methods = ['left', 'right', 'inner', 'outer']
        indexes = [221, 222, 223, 224]

        combinations = [('checkins', 'checkpoints'),
                        ('checkins', 'orders'),
                        ('orders', 'clients')]

        for left, right in combinations:
            title = '+'.join([left, right])
            fig = self.prepare_image(title)

            for index, method in zip(indexes, methods):
                key = right[:-1] + '_id'
                joined = merge(left=self.db[left],
                               right=self.db[right],
                               left_on=key,
                               right_on=key,
                               how=method)

                null_values = joined.isnull().sum()

                if DEBUG:
                    print_header(method)
                    print(joined.reset_index().info())

                null_values.plot(kind='bar',
                                 sharey=True,
                                 sharex=True,
                                 ylim=(0, self.db[left].shape[0]),
                                 axes=fig.add_subplot(index, title=method))

        self.make_image('masked_db.png')

    def missing_prices(self):
        """ Count orders where the price is missing. """

        prices = self.db['orders'][['city_tour',
                                    'overnight',
                                    'waiting_time',
                                    'extra_stops',
                                    'fax_confirm']]

        total = prices.replace(nan, 0).sum(axis=1)
        zeros = total.apply(lambda x: int(not bool(x)))

        print_header('Missing prices')
        print('Number of missing prices: %s' % zeros.sum())

    def missing_overnights(self):
        pass


def inspect():
    """ Run all inspection tests in the module. """
    user = User(db_file='m-134-v2.sqlite')
    q = Inspector(user.db)
    q.missing_prices()
    q.db_info()
    q.empty_cells()
    q.table_joins()

if __name__ == '__main__':
    inspect()


