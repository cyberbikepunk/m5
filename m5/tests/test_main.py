""" Unit tests for the main module (the command line interface). """

from pprint import pprint
import sys
from os.path import abspath
sys.path.append(abspath('..'))
pprint(sys.path)

from unittest import TestCase
from main import apply_parser


def _squeeze(args):
    args = vars(args)
    return dict(arg for (arg, value) in args.items() if value is not None)


#     USAGE = {'fetch_default': {'in': 'm5 fetch',
#                                'out': ''},
#              'fetch_verbose': {'in': 'm5 fetch -v',
#                                'out': ''},
#              'fetch_since': {'in': 'fetch --since 21-02-2012',
#                              'out': ''},
#              'visualize': {'in': 'visualize',
#                            'out': ''},
#              'inspect': {'in': 'inspect',
#                          'out': ''},
#              'visualize_year': {'in': 'visualize -year 2012',
#                                 'out': ''},
#              'visualize_month': {'in': 'visualize -month 03-2014',
#                                  'out': ''},
#              'visualize_day': {'in': 'visualize -day 04-04-2015',
#                                'out': ''},
#              'visualize_help': {'in': 'visualize -h',
#                                 'out': ''}}
#
# class FetchDefault(TestMain):
#     cmd = 'm5 fetch'
#     parser
#
#
# class FetchVerbose(TestMain):
#     cmd =
#
class TestMain(TestCase):

    def test_apply_parser_withoutArguments_printsHelp(self):
        args = apply_parser(['show', '-day', '21-03-2014'])
        pprint(vars(args))

