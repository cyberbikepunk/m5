""" Various unittest scripts for the model module. """

from unittest import TestCase
from sqlalchemy.orm import sessionmaker, session
from sqlalchemy import create_engine
from random import randint, choice, uniform
from uuid import uuid4
from datetime import datetime
from os import remove
from os.path import dirname, join

from m5.model import Checkin, Checkpoint, Client, Order, Base


class TestModel(TestCase):

    def setUp(self):
        """  Set up a temporary database. """

        self.path = join(dirname(__file__), 'temp', 'db-sqlite')
        engine = create_engine('sqlite:///%s' % self.path, echo=False)

        Base.metadata.create_all(engine)

        _Session = sessionmaker(bind=engine)
        self.session = _Session()

    def tearDown(self):
        """  Delete the temporary database. """
        remove(self.path)

    def testCalculation(self):
        """  Fill row objects with random but self-consistent madness. """

        # Tables
        clients = list()
        orders = list()
        checkpoints = list()
        checkins = list()

        # Foreign keys
        checkpoint_ids = list()
        client_ids = list()
        order_ids = list()

        # Random madness
        max_int = 1000000000000000

        for i in range(10):
            client_ids.append(randint(1, max_int))
            clients.append(Client(client_id=client_ids[i],
                                  name=str(uuid4())))

        for i in range(10):
            order_ids.append(randint(1, max_int))
            orders.append(Order(order_id=order_ids[i],
                                distance=uniform(0, 20),
                                cash=choice([True, False]),
                                type=choice(['city_tour', 'overnight', 'help']),
                                client_id=choice(client_ids)))

        for i in range(10):
            checkpoint_ids.append(randint(1, max_int))
            checkpoints.append(Checkpoint(checkpoint_id=checkpoint_ids[i],
                                          company=str(uuid4()),
                                          lat=0,
                                          lon=0))

        for i in range(10):
            checkins.append(Checkin(checkin_id=randint(1, max_int),
                                    purpose=choice(['pickup', 'dropoff']),
                                    order_id=choice(order_ids),
                                    checkpoint_id=choice(checkpoint_ids),
                                    timestamp=datetime.now()))

        # Stage the data
        self.session.add_all(clients)
        self.session.add_all(orders)
        self.session.add_all(checkpoints)
        self.session.add_all(checkins)

        # Feed the beast
        self.session.commit()