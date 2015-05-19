#!/usr/bin/env python
""" WELCOME TO M5!

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

from argparse import ArgumentParser, RawDescriptionHelpFormatter, Action
from sys import argv
from time import strptime
from datetime import date
from datetime import datetime
from calendar import monthrange
from textwrap import dedent

from inspector import inspect
from visualizer import visualize as show
from scraper import scrape as fetch
from settings import IS_TEST


class _Dispatcher(Action):
    def __call__(self, parser, namespace, value=None, option=None):
        """ Dispatch a sub-command to its homonymous function, unless it's a test. """

        # TODO Tests should NOT mess up the way a module works
        # We've set up a test trap, however, because we want to
        # avoid calling more code and return information instead.
        if IS_TEST:
            setattr(namespace, self.dest, value)
            return

        namespace.dispatcher(value, self.dest)


def _date(date_string: str) -> date:
    """ Convert a date string into a date object. """
    t = strptime(date_string, '%d-%m-%Y')
    return date(t.tm_year, t.tm_mon, t.tm_mday)


_EARLY = dict(hour=0, minute=0)
_LATE = dict(hour=23, minute=59)


def _day(date_string: str) -> tuple:
    """ Return the first and the last datetime objects of a given day. """
    t = strptime(date_string, '%d-%m-%Y')
    t1 = datetime(t.tm_year, t.tm_mon, t.tm_mday, *_EARLY)
    t2 = datetime(t.tm_year, t.tm_mon, t.tm_mday, *_LATE)
    return t1, t2


def _month(month_string: str) -> tuple:
    """ Return the first and the last datetime objects of a given month. """
    t = strptime(month_string, '%m-%Y')
    nb_days = monthrange(t.tm_year, t.tm_mon)[1]
    t1 = datetime(t.tm_year, t.tm_mon, t.tm_mday, *_EARLY)
    t2 = datetime(t.tm_year, t.tm_mon, nb_days, *_LATE)
    return t1, t2


def _year(year_string: str) -> tuple:
    """ Return the first and last datetime objects of a given year. """
    t = strptime(year_string, '%Y')
    t1 = datetime(t.tm_year, 1, 1, *_EARLY)
    t2 = datetime(t.tm_year, 12, 31, *_LATE)
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
                              type=_date,
                              default=date.today(),
                              dest='date',
                              action=_Dispatcher)

    show_group = show_parser.add_mutually_exclusive_group()

    show_group.add_argument('-year',
                            help='show a year of data, e.g. 2013',
                            type=_year,
                            default=None,
                            dest='year',
                            action=_Dispatcher)

    show_group.add_argument('-month',
                            help='show a month of data, e.g. 03-2013',
                            type=_month,
                            default=None,
                            dest='month',
                            action=_Dispatcher)

    show_group.add_argument('-day',
                            help='show a day of data, e.g. 02-03-2013',
                            type=_day,
                            default=None,
                            dest='day',
                            action=_Dispatcher)

    return parser


def run(args=None):
    """ Read the command line and dispatch the program to the function whose
        name matches the sub-command. No sub-command? Print the help message.
    """

    parser = _build_parser()

    if len(argv) == 1:
        parser.print_help()
        exit(1)

    return parser.parse_args(args=args)


if __name__ == '__main__':
    run()
