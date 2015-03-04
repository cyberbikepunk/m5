""" Miscellaneous utility classes and functions """

from collections import namedtuple
from os.path import splitext, join
from uuid import uuid1

from m5.settings import OUTPUT


#######################
# Named tuple classes #
#######################


Stamped = namedtuple('Stamped', ['stamp', 'data'])
Stamp = namedtuple('Stamp', ['date', 'uuid'])
Tables = namedtuple('Tables', ['clients', 'orders', 'checkpoints', 'checkins'])


##############
# Decorators #
##############


def log_me(f):
    return f


def time_me(f):
    return f


def safe_io(f):
    return f


def safe_request(f):
    return f


#####################
# Utility functions #
#####################


def force_unique(filename: str) -> str:
    """ Return a unique and absolute file path in the output folder. """
    return join(OUTPUT, splitext(filename)[0] + '-' + str(uuid1()) + splitext(filename)[1])
