#!/usr/bin/env python
""" Run the m5 package from the command line. """


from argparse import ArgumentParser, RawDescriptionHelpFormatter
from sys import argv
from time import strptime
from datetime import date
from textwrap import dedent

from inspector import inspect
from visualize import show
from factory import fetch


def make_day(date_string):
    t = strptime(date_string, '%d-%m-%Y')
    return date(t.tm_year, t.tm_mon, t.tm_mday)

examples = \
    """
    examples:
      $ m5 fetch                    fetch today's data...
      $ m5 fetch -v                 ...with the verbose mode on
      $ m5 fetch --s 21-02-2012     fetch all data since 21st February 2012
      $ m5 inspect                  check the overall quality of the data
      $ m5 show                     visualize today's data
      $ m5 show -y 2012             visualize 2012 data
      $ m5 show -m 03-2014          visualize March 2014 data
      $ m5 show -d 04-04-2015       visualize data for the 4th March 2014
      4 m5 show -h                  print the help message for the "show" sub-command
    """


def build_parser():
    """ Construct a parser using the argparse library. """

    # ------------------------ The parser and sub-commands

    parser = ArgumentParser(prog='m5',
                            epilog=dedent(examples),
                            formatter_class=RawDescriptionHelpFormatter)

    subparsers = parser.add_subparsers()
    show_parser = subparsers.add_parser('show')
    inspect_parser = subparsers.add_parser('inspect')
    fetch_parser = subparsers.add_parser('fetch')

    show_parser.set_defaults(func=show)
    inspect_parser.set_defaults(func=inspect)
    fetch_parser.set_defaults(func=fetch)

    show_group = show_parser.add_mutually_exclusive_group()

    fetch_parser.add_argument('-s',
                              help='fetch all your data since that date',
                              type=make_day,
                              default=date.today(),
                              dest='date')

    show_group.add_argument('-y',
                            help='show a year of data, e.g. 2013',
                            type=str,
                            default=None,
                            dest='year')

    show_group.add_argument('-m',
                            help='show a month of data, e.g. 03-2013',
                            type=str,
                            default=None,
                            dest='month')

    show_group.add_argument('-d',
                            help='show a day of data, e.g. 02-03-2013',
                            type=str,
                            default=None,
                            dest='day')

    parser.add_argument('-v',
                        help='run the program in verbose mode',
                        action='store_const',
                        default=False,
                        const=True)

    return parser


def apply_parser(parser):
    """ Parse the command line arguments. If the script is called with no arguments, print the help message."""

    if len(argv) == 1:
        parser.print_help()
        exit(1)

    args = parser.parse_args()
    args.func()
    return args

if __name__ == '__main__':
    p = build_parser()
    namespace = apply_parser(p)
    print(namespace)
