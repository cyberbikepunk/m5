"""  The module that produces statistics, maps and plots. """


from m5.model import Order, Checkin, Checkpoint, Client
from sqlalchemy.orm.session import Session as DatabaseSession
from m5.user import User
from pandas import DataFrame
from matplotlib.pyplot import show


class Stats():

    def __init__(self, database_session: DatabaseSession):
        """ Instantiate a Stats object

        :param database_session: the current user's database session
        :return:
        """

        self.session = database_session
        self.engine = engine

    def get_frames(self):
        query = self.session.query(Order).order_by(Order.id)
        data_records = [rec.__dict__ for rec in query.all()]
        df = DataFrame.from_records(data_records)
        print(df.head(10))
        print(df.tail(10))

        #df.plot(kind='scatter', x='distance', y='city_tour')
        #show()

        df.plot(kind='hist')
        show()


if __name__ == '__main__':
    u = User('m-134', 'PASSWORD')
    s = Stats(u.database_session, u.engine)

    s.get_frames()