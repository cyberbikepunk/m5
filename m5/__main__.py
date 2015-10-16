#!/usr/bin/env python
""" The command line API for the M5 package. """


from argparse import ArgumentParser, RawDescriptionHelpFormatter
from logging import basicConfig, INFO, DEBUG, info
from datetime import date
from textwrap import dedent
from time import strptime
from datetime import timedelta

from m5.scraper import scrape
from m5.pipeline import process, archive
from m5.spider import download
from m5.settings import LOGGING_FORMAT
from m5.user import User


def setup_logger(verbose):
    basicConfig(level=DEBUG if verbose else INFO, format=LOGGING_FORMAT)


def migrate(**options):
    """ Migrate user data from the company website to the local database. """

    start_date = options.pop('begin')
    stop_date = options.pop('end')
    period = stop_date - start_date

    user = User(**options).init()

    info('User %s is %s', options['username'], 'offline' if options['offline'] else 'online')
    info('Migrating data from %s to %s', start_date, stop_date)

    for day in range(period.days):
        date_ = start_date + timedelta(days=day)
        webpages = download(date_, user)

        for webpage in webpages:
            job = scrape(webpage)
            tables = process(job)
            archive(user.db, tables)

    user.logout()
    info('Finished the migration process')


def build_parser():
    p = ArgumentParser(prog='m5',
                       description=dedent(__doc__),
                       formatter_class=RawDescriptionHelpFormatter,
                       fromfile_prefix_chars='@',
                       epilog='To read arguments from file pass @/absolute/path/to/file.ini')

    p.add_argument('-u',
                   help='username for the bammboo-mec.de website',
                   type=str,
                   default=None,
                   dest='username')

    p.add_argument('-p',
                   help='password for the bammboo-mec.de website',
                   type=str,
                   default=None,
                   dest='password')

    p.add_argument('-v',
                   help='verbose mode on',
                   default=False,
                   action='store_true',
                   dest='verbose')

    p.add_argument('-o',
                   help='offline mode on',
                   default=False,
                   action='store_true',
                   dest='offline')

    def calendar_day(date_string):
        t = strptime(date_string, '%d-%m-%Y')
        day = date(t.tm_year, month=t.tm_mon, day=t.tm_mday)
        if day > date.today():
            raise ValueError
        return day

    p.add_argument('-b',
                   help='migrate data since dd-mm-yyyy (default to today)',
                   type=calendar_day,
                   default=date.today(),
                   dest='begin')

    p.add_argument('-e',
                   help='migrate data until dd-mm-yyyy (defauls to today)',
                   type=calendar_day,
                   default=date.today(),
                   dest='end')

    return p


if __name__ == '__main__':
    parser = build_parser()
    args = parser.parse_args()
    setup_logger(args.verbose)
    migrate(**vars(args))
