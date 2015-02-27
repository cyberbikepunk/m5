"""  The module that produces statistics, maps and plots. """

from m5.model import Order, Checkin, Checkpoint, Client
from sqlalchemy.orm.session import Session
from m5.user import User
from pandas import DataFrame, set_option
import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy.engine import Engine
from m5.utilities import DEBUG
from datetime import date


class Stats():

    def __init__(self, session: Session, engine: Engine):
        """ Pull the data from the database. Tables are stored as pandas dataframes. """

        self.session = session
        self.engine = engine

        self.orders = None
        self.clients = None
        self.checkins = None
        self.checkpoints = None

    def read_orm(self):

        query = self.session.query(Order)
        data = [rec.__dict__ for rec in query.all()]
        orders = DataFrame.from_records(data)
        self.orders = orders.drop('_sa_instance_state', 1)

        query = self.session.query(Client)
        data = [rec.__dict__ for rec in query.all()]
        clients = DataFrame.from_records(data)
        self.clients = clients.drop('_sa_instance_state', 1)

        query = self.session.query(Checkin)
        data = [rec.__dict__ for rec in query.all()]
        checkins = DataFrame.from_records(data)
        self.checkins = checkins.drop('_sa_instance_state', 1)

        query = self.session.query(Checkpoint)
        data = [rec.__dict__ for rec in query.all()]
        checkpoints = DataFrame.from_records(data)
        self.checkpoints = checkpoints.drop('_sa_instance_state', 1)
        self.checkpoints = checkpoints.drop('display_name', 1)

        set_option('display.width', 300)
        print(self.checkpoints.head(10), end='\n\n')
        print(self.checkins.head(10), end='\n\n')
        print(self.orders.head(10), end='\n\n')
        print(self.clients.head(10), end='\n\n')

    def read_sql(self):
        """ Read-out all the tables from the database. """

        self.clients = pd.read_sql_table('client', self.engine, index_col='client_id')
        self.orders = pd.read_sql('order', self.engine, index_col='order_id', parse_dates=['date'])
        self.checkins = pd.read_sql('checkin', self.engine, index_col='timestamp', parse_dates=['timestamp', 'after_', 'until'])
        self.checkpoints = pd.read_sql('checkpoint', self.engine, index_col='checkpoint_id')

        if DEBUG:
            pd.set_option('display.width', 300)
            pd.set_option('max_columns', 20)

            print(self.clients)
            print(self.orders)
            print(self.checkins)
            print(self.checkpoints)

    def make_timeseries(self):

        self.orders['price'] = self.orders['city_tour'] + \
                               self.orders['overnight'] + \
                               self.orders['waiting_time'] + \
                               self.orders['extra_stops'] + \
                               self.orders['fax_confirm']


        income = self.orders.groupby('date').sum()
        income = income[date(2014, 1, 1):date(2014, 12, 30)]
        print(income)

        # timeseries['day'] = timeseries.index.day
        # timeseries['month'] = timeseries.index.month
        # timeseries['year'] = timeseries.index.year

        # fig = plt.figure()
        # ax = fig.add_subplot(2, 1, 1)
        # print(fig)
        # print(ax)
        # fig.show()
        plt.bar(left=income.index.values, height=income.price.values)
        plt.show()

    def diagnose(self):
        """ Check the quality of the data. """

        print('Clients: {shape}'.format(shape=self.clients.shape))
        print('Orders: {shape}'.format(shape=self.orders.shape))
        print('Checkins: {shape}'.format(shape=self.checkins.shape))
        print('Checkpoints: {shape}'.format(shape=self.checkpoints.shape))

        nb_orders = self.orders.count(axis=0, numeric_only=False)
        nb_clients = self.clients.count(axis=0)
        nb_checkins = self.checkins.count(axis=0)
        nb_checkpoints = self.checkpoints.count(axis=0)

        nb_orders = nb_orders.to_frame(name='count')
        nb_clients = nb_clients.to_frame(name='count')
        nb_checkins = nb_checkins.to_frame(name='count')
        nb_checkpoints = nb_checkpoints.to_frame(name='count')

        def percentage(count, total=None):
            return (1 - count/total) * 100

        nb_orders['NaN (%)'] = nb_orders.apply(percentage, total=self.orders.shape[0])
        nb_clients['NaN (%)'] = nb_clients.apply(percentage, total=self.clients.shape[0])
        nb_checkins['NaN (%)'] = nb_checkins.apply(percentage, total=self.checkins.shape[0])
        nb_checkpoints['NaN (%)'] = nb_checkpoints.apply(percentage, total=self.checkpoints.shape[0])

        print(nb_orders, end='\n\n')
        print(nb_clients, end='\n\n')
        print(nb_checkins, end='\n\n')
        print(nb_checkpoints, end='\n\n')

        print(self.orders.groupby('overnight').size(), end='\n\n')
        print(self.orders.groupby('fax_confirm').size(), end='\n\n')
        print(self.orders.groupby('waiting_time').size(), end='\n\n')
        print(self.orders.groupby('city_tour').size(), end='\n\n')
        print(self.orders.groupby('extra_stops').size(), end='\n\n')
        print(self.checkpoints.groupby('postal_code').size(), end='\n\n')
        print(self.orders.groupby('client_id').size(), end='\n\n')

        # city_tours = self.orders.groupby('city_tour').size().replace(0, None).values
        # plt.hist(city_tours, bins=np.linspace(0, 40, 40))
        # plt.show()

        # days = self.orders.groupby('date').sum()
        # print(days)

        # c = self.orders.groupby('city_tour').size()
        # plt.hist(self.orders.city_tour, bins=np.linspace(0, 40, 20))
        # plt.show()

        print(self.orders.city_tour.values)
        plt.bar(left=self.orders.date.values, height=self.orders.city_tour.values)
        plt.show()

        # totals = self.orders.sum(axis=0)
        # print(totals)
        # plt.pie(totals)
        # plt.show()

        # days.plot(kind='bar', x='date', y='city_tour')
        # plt.show()

        # c = self.orders.groupby('city_tour').size()
        # plt.figure()
        # c.to_frame().hist()
        # plt.show()

        # plt.figure()
        # self.orders.plot()
        # plt.show()
        #
        # a = self.orders['overnight']
        # b = a.replace(0, 'zero')
        # print(a)
        # print(b)

    def basics(self):
        """ Print out basic statistics and plot simple graphs. """

        print(self.orders[['city_tour', 'distance']].describe(), end='\n\n')
        print(self.checkins['timestamp'].describe(), end='\n\n')
        print(self.orders.sum(), end='\n\n')

        self.orders.plot(kind='scatter', x='distance', y='city_tour')
        show()

        self.orders.plot(kind='scatter', x='order_id', y='city_tour')
        show()

        postalcodes = self.checkpoints.groupby('postal_code')
        print(postalcodes.head(10))


if __name__ == '__main__':
    u = User('m-134', 'PASSWORD', local=True)
    s = Stats(u.database_session, u.engine)
    s.read_sql()
    s.make_timeseries()