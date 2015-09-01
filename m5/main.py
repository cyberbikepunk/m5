#!/usr/bin/env python
""" The command line API for the M5 package. """


from argparse import ArgumentParser, RawDescriptionHelpFormatter
from logging import basicConfig, INFO, DEBUG, info
from datetime import date
from textwrap import dedent
from time import strptime

from m5.threads import run


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


def setup_logger(verbose):
    basicConfig(level=DEBUG if verbose else INFO,
                format='M5 '
                       '[%(asctime)s] '
                       '[%(module)s] '
                       '[%(funcName)s] '
                       '%(message)s')


def calendar_day(date_string):
    t = strptime(date_string, '%d-%m-%Y')
    day = date(t.tm_year, month=t.tm_mon, day=t.tm_mday)

    if day > date.today():
        raise ValueError

    return day


if __name__ == '__main__':
    parser = build_parser()
    args = parser.parse_args()
    setup_logger(args.verbose)
    info('Arguments = %s', args)
    run(**vars(args))
