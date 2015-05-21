""" Nosetests for the command line interface. """

from nose.plugins.skip import SkipTest

from main import parse
from settings import BLINK, TODAY, SINCE, YEAR, MONTH, DAY
from inspector import inspect
from visualizer import visualize as show
from scraper import scrape as fetch

import sys

# Tests live in a folder alongside the tested module
sys.path.extend(['./../..'])


class TestParser():
    COMMANDS = list()
    ANSWERS = list()

    def __init__(self):
        self.dispatcher = None
        self.options = dict()
        self.answer = dict()

    # FIXME Work-around compensates the behaviour of the nosetest generator.
    # This is very ugly. I have to pass the object method and the object state
    # seperately because nosetests instantiate a new object each time around.
    # I'm cheating python by calling the _checklist() method a static method.

    @staticmethod
    def _checklist(self):
        pass

    def test(self):
        for command, self.answer in zip(self.COMMANDS, self.ANSWERS):
            _, self.dispatcher, self.options = parse(command.split())
            yield self._checklist, self


class TestParserWithAllowedCommands(TestParser):
    COMMANDS = ['fetch',
                'fetch -since 21-02-2012',
                'show',
                'inspect',
                'show -year 2012',
                'show -month 03-2014',
                'show -day 04-04-2015']

    ANSWERS = [{'dispatcher': fetch, 'options': {'since': TODAY}},
               {'dispatcher': fetch, 'options': {'since': SINCE}},
               {'dispatcher': show, 'options': {'day': TODAY}},
               {'dispatcher': inspect, 'options': {'day': TODAY}},
               {'dispatcher': show, 'options': {'year': YEAR}},
               {'dispatcher': show, 'options': {'month': MONTH}},
               {'dispatcher': show, 'options': {'day': DAY}}]

    @staticmethod
    def _checklist(self):
        return all([self.dispatcher,
                    self._check_options(),
                    self._check_values()])

    def _check_dispatcher(self):
        return self.dispatcher is self.answer['dispatcher']

    def _check_options(self):
        return set(self.options.keys()) == set(self.answer['options'].keys())

    def _check_values(self):
        return all([self._compare(value, self.answer['options'][key], key)
                    for key, value in self.options.items()])

    @staticmethod
    def _compare(a, b, option):
        if option in ('day', 'month', 'year'):
            return all([a[0]-b[0] < BLINK, a[1]-b[1] < BLINK])
        elif option is 'since':
            return a-b < BLINK
        else:
            print('not found')
            return False