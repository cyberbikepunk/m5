#!/usr/bin/env python
""" The command line API for the M5 package. """


from argparse import ArgumentParser, RawDescriptionHelpFormatter
from logging import basicConfig, INFO, DEBUG
from datetime import date
from textwrap import dedent
from time import strptime

from logging import info
from datetime import timedelta

from m5.user import initialize
from m5.scraper import scrape
from m5.pipeline import process, archive
from m5.spider import download
from m5.settings import LOGGING_FORMAT


def setup_logger():
    basicConfig(level=DEBUG if args.verbose else INFO,
                format=LOGGING_FORMAT)


def migrate(**options):
    """ Migrate user data from the company website to the local database. """

    info('Starting migration process')

    start_date = options.pop('begin')
    stop_date = options.pop('end')
    period = stop_date - start_date

    user = initialize(**options)

    for day in range(period.days):
        date_ = start_date + timedelta(days=day)
        webpages = download(date_, user)

        for webpage in webpages:
            job = scrape(webpage)
            tables = process(job)
            archive(user.db, tables)

    info('Finished the migration process')
    user.logout()


def build_parser():
    p = ArgumentParser(prog='m5',
                       description=dedent(__doc__),
                       formatter_class=RawDescriptionHelpFormatter,
                       fromfile_prefix_chars='@',
                       epilog='To read arguments from file, type: m5 @/absolute/path/to/file.')

    p.add_argument('-u',
                   help='username for the company website',
                   type=str,
                   default=None,
                   dest='username')

    p.add_argument('-p',
                   help='password for the company website',
                   type=str,
                   default=None,
                   dest='password')

    p.add_argument('-v',
                   help='switch the verbose mode on',
                   default=False,
                   action='store_true',
                   dest='verbose')

    p.add_argument('-o',
                   help='switch the offline mode on',
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
                   help='scrape all data since dd-mm-yyyy',
                   type=calendar_day,
                   default=date.today(),
                   dest='begin')

    p.add_argument('-e',
                   help='scrape all data until dd-mm-yyyy',
                   type=calendar_day,
                   default=date.today(),
                   dest='end')

    return p


if __name__ == '__main__':
    setup_logger()

    parser = build_parser()
    args = parser.parse_args()

    info('User %s is %s', args.username, 'offline' if args.offline else 'online')
    info('Scraping from %s to %s', args.begin, args.end)

    migrate(**vars(args))
