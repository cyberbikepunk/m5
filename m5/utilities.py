""" Miscellaneous utility classes decorators and functions """

from collections import namedtuple
from datetime import datetime
from os.path import splitext, join, getctime, isdir
from os import mkdir
from glob import iglob
from re import sub

from m5.settings import USER, OUTPUT, DATABASE, DOWNLOADS, TEMP, LOG


# --------------------- NAMED TUPLES


Stamped = namedtuple('Stamped', ['stamp', 'data'])
Stamp = namedtuple('Stamp', ['date', 'uuid'])
Tables = namedtuple('Tables', ['clients', 'orders', 'checkpoints', 'checkins'])

# --------------------- DECORATORS


def log_me(f):
    return f


def time_me(f):
    return f


# --------------------- FUNCTIONS


def unique_file(name: str) -> str:
    """ Return a unique path in the output folder. """

    (base, extension) = splitext(name)
    stamp = sub(r'[:]|[-]|[_]|[.]|[\s]', '', str(datetime.now()))
    unique = base.ljust(20, '_') + stamp + extension
    path = join(OUTPUT, unique)

    return path


def latest_file(folder: str):
    """ Return the most recent file inside the folder. """
    return min(iglob(join(folder, '*.sqlite')), key=getctime)


def check_folders():
    """ Create user folders if needed. """

    folders = (USER, OUTPUT, DATABASE, DOWNLOADS, TEMP, LOG)

    for folder in folders:
        if not isdir(folder):
            # Don't handle IO exception
            # to get deeper feedback.
            mkdir(folder, mode=775)
            print('Created {dir}.'.format(dir=folder))


if __name__ == '__main__':
    print(latest_file(DATABASE))
    print(unique_file('example.yo'))