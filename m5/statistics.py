"""  The module that produces statistics, maps and plots. """

from m5.model import Order, Checkin, Checkpoint, Client
from sqlalchemy.orm.session import Session
from m5.user import User
from pandas import DataFrame, set_option
from matplotlib.pyplot import show


class Stats():

    def __init__(self, session: Session):
        """ Pull the data from the database. Tables are saved as Pandas dataframes. """

        self.session = session

        query = self.session.query(Order)
        data = [rec.__dict__ for rec in query.all()]
        self.orders = DataFrame.from_records(data)
        self.orders = self.orders.drop('_sa_instance_state', 1)

        query = self.session.query(Client)
        data = [rec.__dict__ for rec in query.all()]
        self.clients = DataFrame.from_records(data)
        self.clients = self.clients.drop('_sa_instance_state', 1)

        query = self.session.query(Checkin)
        data = [rec.__dict__ for rec in query.all()]
        self.checkins = DataFrame.from_records(data)
        self.checkins = self.checkins.drop('_sa_instance_state', 1)

        query = self.session.query(Checkpoint)
        data = [rec.__dict__ for rec in query.all()]
        self.checkpoints = DataFrame.from_records(data)
        self.checkpoints = self.checkpoints.drop('_sa_instance_state', 1)

        set_option('display.width', 300)
        print(self.checkpoints.head(10))
        print(self.checkpoints.tail(10))

        self.orders.plot(kind='scatter', x='distance', y='city_tour')
        show()

if __name__ == '__main__':
    u = User('m-134', 'PASSWORD')
    s = Stats(u.database_session)