#!/usr/bin/env python
"""
WELCOME TO M5!

usage examples:
  m5                              print the help message
  m5 fetch                        scrape today's data
  m5 fetch --since 21-02-2012     scrape data since 21 Feb 2012
  m5 show                         visualize today's data
  m5 show -year 2012              visualize 2012 data
  m5 show -month 03-2014          visualize data for Mar 2014
  m5 show -day 04-04-2015         visualize data for 4 Mar 2014
  m5 show -h                      print help for 'show'
  m5 inspect                      'inspect' works just like 'show'
"""

from argparse import ArgumentParser, RawDescriptionHelpFormatter
from time import strptime
from datetime import date
from datetime import datetime
from calendar import monthrange
from textwrap import dedent

from inspector import inspect
from visualizer import visualize as show
from scraper import scrape as fetch
from settings import EARLY, LATE


def _since(date_string: str) -> date:
    """ Convert a date string into a date object. """
    t = strptime(date_string, '%d-%m-%Y')
    return date(t.tm_year, t.tm_mon, t.tm_mday)


def _day(date_string) -> (datetime, datetime):
    """ Return the first and the last datetime objects of a given day. """
    t = strptime(date_string, '%d-%m-%Y')
    t1 = datetime(t.tm_year, t.tm_mon, t.tm_mday, **EARLY)
    t2 = datetime(t.tm_year, t.tm_mon, t.tm_mday, **LATE)
    return t1, t2


def _month(month_string) -> (datetime, datetime):
    """ Return the first and the last datetime objects of a given month. """
    t = strptime(month_string, '%m-%Y')
    nb_days = monthrange(t.tm_year, t.tm_mon)[1]
    t1 = datetime(t.tm_year, t.tm_mon, t.tm_mday, **EARLY)
    t2 = datetime(t.tm_year, t.tm_mon, nb_days, **LATE)
    return t1, t2


def _year(year_string) -> (datetime, datetime):
    """ Return the first and last datetime objects of a given year. """
    t = strptime(year_string, '%Y')
    t1 = datetime(t.tm_year, 1, 1, **EARLY)
    t2 = datetime(t.tm_year, 12, 31, **LATE)
    return t1, t2


def _build_parser():
    """ Construct the command line parser. """

    parser = ArgumentParser(prog='m5',
                            description=dedent(__doc__),
                            formatter_class=RawDescriptionHelpFormatter)

    subparsers = parser.add_subparsers()

    show_parser = subparsers.add_parser('show')
    fetch_parser = subparsers.add_parser('fetch')
    inspect_parser = subparsers.add_parser('inspect')

    fetch_parser.set_defaults(dispatcher=fetch)
    show_parser.set_defaults(dispatcher=show)
    inspect_parser.set_defaults(dispatcher=inspect)

    fetch_parser.add_argument('-since',
                              help='fetch all your data since that date',
                              type=_since,
                              default=date.today(),
                              dest='since')

    show_group = show_parser.add_mutually_exclusive_group()

    show_group.add_argument('-year',
                            help='show a year of data, e.g. 2013',
                            type=_year,
                            dest='year')

    show_group.add_argument('-month',
                            help='show a month of data, e.g. 03-2013',
                            type=_month,
                            dest='month')

    show_group.add_argument('-day',
                            help='show a day of data, e.g. 02-03-2013',
                            type=_day,
                            dest='day')

    return parser


def _extract(namespace):
    """ Extract the dispatcher function and its options. """

    if hasattr(namespace, 'dispatcher'):
        dispatcher = namespace.dispatcher
    else:
        dispatcher = None

    options = {key: value
               for (key, value)
               in vars(namespace).items()
               if value and key != 'dispatcher'}

    return dispatcher, options


def parse(args: list=None):
    """ Interpret the command line. """

    parser = _build_parser()
    namespace = parser.parse_args(args=args)
    dispatcher, options = _extract(namespace)

    return parser.print_help, dispatcher, options


def _run(args: list=None):
    """ Dispatch the program to the right place or print the help message. """

    helper, dispatcher, options = parse(args)

    if dispatcher:
        dispatcher(**options)
    else:
        helper()


if __name__ == '__main__':
    _run()
