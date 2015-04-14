#!/usr/bin/python3
""" Run the m5 package from the command line. """

from argparse import ArgumentParser, RawDescriptionHelpFormatter
from datetime import date
from textwrap import dedent
from sys import path

# if '.' not in path:
path.append('.')
print(path)
from m5.factory import bulk_download, process


parser = ArgumentParser(prog='m5', formatter_class=RawDescriptionHelpFormatter,
                        description=dedent("""\nAnalyze your bike messenger data
                                               --------------------------------
                                               You must have a login and password
                                               for the bamboo-mec.de server. """))

subparsers = parser.add_subparsers()

# create the parser for the "download" command
parser_foo = subparsers.add_parser('download')
parser_foo.add_argument('begin', type=str, default=None)
parser_foo.set_defaults(func=bulk_download)

# create the parser for the "process" command
parser_foo = subparsers.add_parser('process')
parser_foo.add_argument('begin', type=str, default=None)
parser_foo.set_defaults(func=process)

# create the parser for the "show" command
parser_foo = subparsers.add_parser('show')
parser_foo.add_argument('-y', type=str, default=None, help='a year like 2013')
parser_foo.add_argument('-m', type=str, default=None, help='a numeric month like 11')
parser_foo.add_argument('-d', type=str, default=None, help='a numeric day like 28')
parser_foo.set_defaults(func=process)

parser.add_argument('-debug',
                    metavar='verbose option',
                    type=bool,
                    default=False,
                    help='print verbose to standard output')

parser.add_argument('-pop',
                    metavar='pop option',
                    type=bool,
                    default=False,
                    help='pop the figure windows')

parser.add_argument('-offlibe',
                    metavar='offline option',
                    type=bool,
                    default=False,
                    help='local database connection only')

print(parser)