"""  The module that produces statistics, maps and plots. """


from m5.model import Order, Checkin, Checkpoint, Client
from sqlalchemy.orm.session import Session as DatabaseSession
from m5.user import User


class Stats():

    def __init__(self, database_session: DatabaseSession):
        self.session = database_session

    def play(self):

        for instance in self.session.query(Client).order_by(Client.id):
            print(instance.id, instance.name)

        for instance in self.session.query(Order).order_by(Order.id):
            print(instance.id, instance.date)

        for instance in self.session.query(Checkin).order_by(Checkin.id):
            print(instance.id, instance.timestamp)

        for instance in self.session.query(Checkpoint).order_by(Checkpoint.postal_code):
            print(instance.postal_code, instance.street)

        for instance in self.session.query(Order).filter(Order.cash is True).order_by(Order.id):
            print(instance.id, instance.date)

if __name__ == '__main__':
    u = User('m-134', 'PASSWORD')
    s = Stats(u.database_session)

    s.play()