""" Small scripts using the m5 module API. """

from m5.user import User
from m5.factory import Miner, Factory
from datetime import date, timedelta


def bulk_download():

    u = User('m-134', 'PASSWORD')
    m = Miner(u.remote_session, u.username)

    start = date(2013, 3, 1)
    end = date(2014, 12, 24)
    delta = end - start

    soups = list()
    for n in range(delta.days):
        day = start + timedelta(days=n)
        soup = m.mine(day)
        soups.append(soup)

    return soups


def bulk_migrate():

    u = User('m-134', 'PASSWORD')
    factory = Factory(u)

    start = date(2013, 3, 1)
    stop = date(2014, 12, 24)

    factory.migrate(start, stop)
    

if __name__ == '__main__':
    bulk_migrate()
