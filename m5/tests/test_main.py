""" Unit tests for the main module (the command line interface). """

# This is ugly
path.append('./../..')

from datetime import datetime, date
from sys import path
from main import run

_early = dict(hour=0, minute=0)
_late = dict(hour=23, minute=59)

_TODAY = date.today()
_02_21_2012 = date(2012, 2, 21)
_2012 = (datetime(2012, 1, 1, *_early), datetime(2012, 12, 31, *_late))
_03_2014 = datetime(2012, 3, 1, *_early), datetime(2012, 3, 31, *_late)
_04_04_2015 = datetime(2012, 4, 4, *_early), datetime(2012, 4, 4, *_late)

INPUT = ['m5 fetch',
         'fetch --since 21-02-2012',
         'visualize',
         'inspect',
         'show -year 2012',
         'show -month 03-2014',
         'show -day 04-04-2015']

OUTPUT = [{'since': _TODAY, 'dispatcher': 'scrape'},
          {'since': _02_21_2012, 'dispatcher': 'scrape'},
          {'day': _TODAY, 'dispatcher': 'visualize'},
          {'day': _TODAY, 'dispatcher': 'inspect'},
          {'year': _2012, 'dispatcher': 'visualize'},
          {'month': _03_2014, 'dispatcher': 'visualize'},
          {'day': _04_04_2015, 'dispatcher': 'visualize'}]

USAGE = zip(INPUT, OUTPUT)


class TestMain():

    @staticmethod
    def _repackage(args):
        cleaned = {key: value for (key, value) in vars(args).items() if value}
        return cleaned

    @test
    def applyparser_allowedsubcommand_dispatchesfunction(self):
        for in_, out in enumerate(USAGE):
            yield self._compare, self._run(in_), out

    @staticmethod
    def _compare(input_, output):
        assert input_ == output

    @staticmethod
    def _run(subcommand):
        namespace = run(subcommand)
        return vars(namespace)
