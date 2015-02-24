""" Miscellaneous utility classes and functions """

from datetime import datetime
from collections import namedtuple

DEBUG = True

Stamped = namedtuple('Stamped', ['stamp', 'data'])
Stamp = namedtuple('Stamp', ['date', 'uuid'])
Tables = namedtuple('Tables', ['clients', 'orders', 'checkpoints', 'checkins'])


def log_me(f):
    return f


def time_me(f):
    return f


def safe_io(f):
    return f


def safe_request(f):
    return f


def notify(message, *args):
    """ Print a message to the screen. """

    message = message.format(*args)
    timestamp = '{:%Y-%m-%d %H:%M}'.format(datetime.now())
    print('%s | %s' % (timestamp, message))


