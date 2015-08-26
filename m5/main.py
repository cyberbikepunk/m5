#!/usr/bin/env python
""" The command line API module for the M5 package. """


from argparse import ArgumentParser, RawDescriptionHelpFormatter
from logging import basicConfig, INFO, DEBUG, debug, info
from datetime import date
from textwrap import dedent
from timestring import Date

from m5.scraper import scrape


def setup_logger(verbose):
    basicConfig(level=DEBUG if verbose else INFO,
                format='M5 '
                       '[%(asctime)s] '
                       '[%(module)s] '
                       '[%(funcName)s] '
                       '%(message)s')


def build_parser():
    p = ArgumentParser(prog='m5',
                       description=dedent(__doc__),
                       formatter_class=RawDescriptionHelpFormatter,
                       fromfile_prefix_chars='@')

    p.add_argument('-u', '--username',
                   help='username for the company website',
                   type=str,
                   default=None,
                   dest='username')

    p.add_argument('-p', '--password',
                   help='password for the company website',
                   type=str,
                   default=None,
                   dest='password')

    p.add_argument('-v', '--verbose',
                   help='switch the verbose mode on',
                   default=False,
                   action='store_true')

    p.add_argument('-o', '--offline',
                   help='switch the offline mode on',
                   default=False,
                   action='store_true')

    p.add_argument('-s', '--since',
                   help='scrape all data since that date (dd-mm-YYYY)',
                   type=since,
                   default=date.today(),
                   dest='since')

    return p


def since(date_string):
    day = Date(date_string)
    if day > date.today():
        raise ValueError('Cannot return to the future.')
    return day.date


def get_options(namespace):
    dictionary = {key: value for (key, value) in vars(namespace).items()}
    info('Arguments = %s', dictionary)
    return dictionary.pop('verbose')


if __name__ == '__main__':
    parser = build_parser()
    args = parser.parse_args()
    setup_logger(args.verbose)
    options = get_options(args)
    #scrape(**options)
