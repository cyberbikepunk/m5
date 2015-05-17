#!/usr/bin/env python
"""
WELCOME TO M5!

examples:
  m5 fetch                        fetch today's data...
  m5 fetch -v                     ...with the verbose mode on
  m5 fetch --since 21-02-2012     fetch data since the 21 Feb 2012
  m5 visualize                    visualize today's data
  m5 inspect                      "inspect" works like "visualize"
  m5 visualize -year 2012         visualize 2012 data
  m5 visualize -month 03-2014     visualize data for Mar 2014
  m5 visualize -day 04-04-2015    visualize data for 4 Mar 2014
  m5 visualize -h                 get help for "visualize"
"""

from argparse import ArgumentParser, RawDescriptionHelpFormatter, Action
from sys import argv
from time import strptime
from datetime import date
from datetime import datetime
from calendar import monthrange
from textwrap import dedent

from inspector import inspect
from visualizer import visualize
from scraper import scrape


def _date(date_string: str) -> date:
    """ Convert a date string into a date object. """
    t = strptime(date_string, '%d-%m-%Y')
    return date(t.tm_year, t.tm_mon, t.tm_mday)


def _day(date_string: str) -> tuple:
    """ Return the first and the last datetime objects of a given day. """
    t = strptime(date_string, '%d-%m-%Y')
    d1 = datetime(t.tm_year, t.tm_mon, t.tm_mday)
    d2 = datetime(t.tm_year, t.tm_mon, t.tm_mday, hour=23, minute=59)
    return d1, d2


def _month(month_string: str) -> tuple:
    """ Return the first and the last datetime objects of a given month. """
    t = strptime(month_string, '%m-%Y')
    nb_days = monthrange(t.tm_year, t.tm_mon)[1]
    d1 = datetime(t.tm_year, t.tm_mon, t.tm_mday)
    d2 = datetime(t.tm_year, t.tm_mon, nb_days, hour=23, minute=59)
    return d1, d2


def _year(year_string: str) -> tuple:
    """ Return the first a last datetime objects of a given year. """
    t = strptime(year_string, '%Y')
    d1 = datetime(t.tm_year, 1, 1)
    d2 = datetime(t.tm_year, 12, 31, hour=23, minute=59)
    return d1, d2


class _Dispatch(Action):
    def __call__(self, parser, namespace, parameter=None, option_string=None):
        """ Sub-commands get dispatched to homonymous functions. """
        namespace.dispatcher(parameter, option_string)


def _build_parser():
    """ Construct the command line parser. """

    parser = ArgumentParser(prog='m5',
                            description=dedent(__doc__),
                            formatter_class=RawDescriptionHelpFormatter)

    subparsers = parser.add_subparsers()

    show_parser = subparsers.add_parser('show')
    fetch_parser = subparsers.add_parser('fetch')
    inspect_parser = subparsers.add_parser('inspect')

    fetch_parser.set_defaults(dispatcher=scrape)
    show_parser.set_defaults(dispatcher=visualize)
    inspect_parser.set_defaults(dispatcher=inspect)

    fetch_parser.add_argument('-since',
                              help='fetch all your data since that date',
                              type=_date,
                              default=date.today(),
                              dest='date',
                              action=_Dispatch)

    show_group = show_parser.add_mutually_exclusive_group()

    show_group.add_argument('-year',
                            help='show a year of data, e.g. 2013',
                            type=_year,
                            default=None,
                            dest='year',
                            action=_Dispatch)

    show_group.add_argument('-month',
                            help='show a month of data, e.g. 03-2013',
                            type=_month,
                            default=None,
                            dest='month',
                            action=_Dispatch)

    show_group.add_argument('-day',
                            help='show a day of data, e.g. 02-03-2013',
                            type=_day,
                            default=None,
                            dest='day',
                            action=_Dispatch)

    parser.add_argument('-v',
                        help='run the program in verbose mode',
                        action='store_const',
                        default=False,
                        const=True)

    return parser


def _apply_parser(parser):
    """ Running the script with no arguments prints the help message. """
    if len(argv) == 1:
        parser.print_help()
        exit(1)
    parser.parse_args()


if __name__ == '__main__':
    p = _build_parser()
    _apply_parser(p)
