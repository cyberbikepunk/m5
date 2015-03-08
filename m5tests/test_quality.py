"""  Test the stats module! """

from unittest import TestCase

from m5.model import Order, Checkin, Checkpoint, Client
from m5.user import User
from m5.quality import QualityCheck


class TestStats(TestCase):

    def setUp(self):
        u = User('m-134', 'PASSWORD')
        self.session = u.local_session
        self.engine = u.engine
        self.stats = QualityCheck(u.local_session)

    def tearDown(self):
        pass

    def testStats(self):

        self.stats.check_sums()
        self.stats.summarize_db()

    def testDatabase(self):

        if False:

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

