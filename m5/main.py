#!/usr/bin/env python

"""
--------------------------------
m5 analyses your messenger data.
--------------------------------

You will need your credentials to access the bamboo-mec.de server. Running
the program from the command line is very simple. Here are some examples...

To show this message:
    $ m5

To fetch today's data:
    $ m5 fetch

To fetch all your data since the 21st February 2012:
    $ m5 fetch --since 21-02-2012

To visualize today's data:
    $ m5 visualize

To visualize a particular period of time:
    $ m5 visualize --year 2012
    $ m5 visualize --month 03-2014
    $ m5 visualize --day 04-04-2015

The program stores your data and visualizations in a hidden folder inside
your home directoy (~/.m5/). Make sure your file manager shows hidden files!

Please contact loic.jounot@gmail.com if you encounter problems. Have fun!
"""

from argparse import ArgumentParser
from sys import argv
from datetime import date

today = None


def make_day():
    return


def make_month():
    return


def make_year():
    return


def main():
    """ Parse the command line arguments. If the script is called with no arguments, print the docstring."""

    m5 = ArgumentParser(prog='m5', description='m5 analyses your messenger data.')
    subparsers = m5.add_subparsers()

    # ------------------------ The "fetch" command

    fetch = subparsers.add_parser('fetch')
    fetch.add_argument('--since', type=str, default=None)

    # ------------------------ The "visualize" command

    visualize = subparsers.add_parser('visualize')
    time_delta = visualize.add_mutually_exclusive_group()

    time_delta.add_argument('-y', '--year',
                            help='visualize a year of data',
                            type=str,
                            default=None,
                            dest='time_delta')

    time_delta.add_argument('-m', '--month',
                            help='visualize a month of data',
                            type=str,
                            default=None,
                            dest='time_delta')

    time_delta.add_argument('-d', '--day',
                            help='visualize a day of data',
                            type=str,
                            default=None,
                            dest='time_delta')

    # ------------------------ Option flags

    m5.add_argument('-v', '--verbose',
                    help='run the program in high verbose mode',
                    default=False,
                    action='store_const',
                    const=True)

    m5.add_argument('-o', '--offline',
                    help='connect only to the local database',
                    default=False,
                    action='store_const',
                    const=True)

    # ------------------------ Parse the command line

    if len(argv) == 1:
        print(__doc__)
        exit(1)
    else:
        args = m5.parse_args()
        print(args)


if __name__ == '__main__':
    main()