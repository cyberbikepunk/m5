#!/usr/bin/python3
""" Command line API for the m5 package. """
from argparse import ArgumentParser

from m5.user import User
from m5.factory import Miner, Factory
from m5.settings import show_settings, create_folders, DEBUG

from datetime import date, timedelta


def bulk_download(begin: date=, end: date):
    """ Download all web-pages between two dates. """

    m = Miner(u.remote_session, u.username)

    delta = end - begin

    soups = list()
    for n in range(delta.days):
        day = begin + timedelta(days=n)
        soup = m.mine(day)
        soups.append(soup)

    return soups


def bulk_migrate():

    u = User('m-134', 'PASSWORD')
    factory = Factory(u)

    start = date(2013, 3, 1)
    stop = date(2014, 12, 24)

    factory.migrate(start, stop)


def test_quality():
    u = User('m-134', 'PASSWORD', local=True)
    self.session = u.database_session
    self.engine = u.engine
    self.stats = Stats(u.database_session, u.engine)

if __name__ == '__main__':
    """ Command line execution. """

    parser = ArgumentParser(description='Analyze your bike messenger data.')
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument('download', action='store_true')
    actions.add_argument('migrate', action='store_true')
    parser.add_argument('x', type=int, help='the base')
    parser.add_argument('y', type=int, help='the exponent')
    args = parser.parse_args()

    # Just in case
    create_folders()

    if DEBUG:
        show_settings()

    u = User()

answer = args.x**args.y

if args.quiet:
    print(answer)
elif args.verbose:
    print('{} to the power {} equals {}'.format(args.x, args.y, answer))
else:
    print('{}^{} == {}'.format(args.x, args.y, answer))