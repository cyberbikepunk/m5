#!/usr/bin/env python

"""
WELCOME TO M5!

usage examples:
  m5                              print the help message
  m5 fetch                        scrape today's data
  m5 fetch --since 21-02-2012     scrape data since 21 Feb 2012
  m5 show                         visualize today's data
  m5 show --year 2012             visualize data for the year 2012
  m5 show --month 3               visualize data for the months of March
  m5 show --day 4                 visualize data for the 4th of each month
  m5 show -d 4 -m 3 -y 2012       visualize data for the March 4th 2012
  m5 show --help                  print help for the show command
  m5 check                        check the quality of the data (works just like show)
"""


from configargparse import ArgumentParser, RawDescriptionHelpFormatter
from logging import basicConfig, INFO, DEBUG, debug
from datetime import date
from textwrap import dedent
from timestring import Date

from m5.inspector import inspect as check
from m5.visualizer import visualize as show
from m5.scraper import scrape as fetch
from m5.settings import PROJECT_DIR


def setup_logger(verbose):
    basicConfig(level=DEBUG if verbose else INFO,
                format='M5 '
                       '[%(asctime)s] '
                       '[%(module)s] '
                       '[%(funcName)s] '
                       '%(message)s')


def _build_parser():
    """ Construct the command line parser. """

    parser = ArgumentParser(prog='m5',
                            description=dedent(__doc__),
                            formatter_class=RawDescriptionHelpFormatter,
                            default_config_files=[PROJECT_DIR + '/' + 'settings.ini'])

    parser.add_argument('-u', '--username',
                              help='username for the company website',
                              type=str,
                              default=None,
                              dest='username')

    parser.add_argument('-p', '--password',
                              help='password for the company website',
                              type=str,
                              default=None,
                              dest='password')

    parser.add_argument('-v', '--verbose',
                              help='switch the verbose mode on',
                              default=False,
                              action='store_true')

    parser.add_argument('-o', '--offline',
                        help='switch the offline mode on',
                        default=False,
                        action='store_true')

    subparsers = parser.add_subparsers()

    show_parser = subparsers.add_parser('show')
    fetch_parser = subparsers.add_parser('fetch')
    inspect_parser = subparsers.add_parser('check')

    fetch_parser.set_defaults(dispatcher=fetch)
    show_parser.set_defaults(dispatcher=show)
    inspect_parser.set_defaults(dispatcher=check)

    fetch_parser.add_argument('-s', '-since',
                              help='fetch all your data since that date',
                              type=Date,
                              default=date.today(),
                              dest='since')

    show_parser.add_argument('-y', '-year',
                             help='show data for that year, e.g. 2013',
                             type=int,
                             dest='year')

    show_parser.add_argument('-m', '-month',
                             help='show data for that month, e.g. 03-2013',
                             type=int,
                             dest='month')

    show_parser.add_argument('-d', '-day',
                             help='show data for that day, e.g. 02-03-2013',
                             type=int,
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

    setup_logger(options.pop('verbose'))
    debug('Oprions = %s', str(options))

    return dispatcher, options


def _parse(args: list=None):
    parser = _build_parser()
    namespace = parser.parse_args(args=args)
    dispatcher, options = _extract(namespace)

    return parser.print_help, dispatcher, options


def dispatch(args: list=None):
    """ Dispatch the program to the right place or print the help message. """

    helper, dispatcher, options = _parse(args)

    if dispatcher:
        dispatcher(**options)
    else:
        helper()


if __name__ == '__main__':
    dispatch()
