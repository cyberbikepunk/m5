""" Miscellaneous utility classes decorators and functions """
from pprint import pprint
import fiona

import shapefile
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from matplotlib.collections import PolyCollection
from collections import namedtuple
from datetime import datetime
from os.path import splitext, join, getctime, isdir
from os import mkdir
from glob import iglob
from re import sub
from random import sample

from m5.settings import FILL, USER, OUTPUT, DATABASE, DOWNLOADS, TEMP, LOG, SKIP, CENTER, DBF, SHP


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
    unique = base.ljust(20, FILL) + stamp + extension
    path = join(OUTPUT, unique)

    return path


def latest_file(folder: str):
    """ Return the most recent file inside the folder. """
    return min(iglob(join(folder, '*.sqlite')), key=getctime)


def print_header(title):
    print('{begin}{title:{fill}{align}100}'.format(title=title, fill=FILL, align=CENTER, begin=SKIP), end=SKIP)


def print_pandas(obj, title: str):
    pd.set_option('max_columns', 99)
    print(SKIP)
    print('{title:{fill}{align}100}'.format(title=title, fill=FILL, align=CENTER))
    print(SKIP)
    print(obj.tail(5))
    if isinstance(obj, pd.DataFrame):
        print(SKIP)
        print(obj.info())


def check_install():
    """ Create user folders if needed. """

    folders = (USER, OUTPUT, DATABASE, DOWNLOADS, TEMP, LOG)

    for folder in folders:
        if not isdir(folder):
            # Don't handle IO exception
            # to get deeper feedback.
            mkdir(folder, mode=775)
            print('Created {dir}.'.format(dir=folder))


def check_shapefile():

    shp = open(SHP, 'rb')
    dbf = open(DBF, 'rb')
    sf = shapefile.Reader(shp=shp, dbf=dbf)

    shapes = sf.shapes()
    records = sf.records()

    # READER OBJECT
    print(SKIP)
    print('{title:{fill}{align}100}'.format(title='READER OBJECT (.SHP + .DBF)', fill=FILL, align=CENTER))
    print('Reader.numRecords = %s' % sf.numRecords)
    print('Reader.bbox = %s' % sf.bbox)
    print('Reader.fields = %s' % sf.fields)
    print('Reader.shp = %s' % sf.shp)
    print('Reader.dbf = %s' % sf.dbf)
    print('Reader.shx = %s' % sf.shx)
    print('Reader.shapeType = %s' % sf.shapeType)
    print('Reader.shpLength = %s' % sf.shpLength)

    # SHAPES OBJECTS
    print(SKIP)
    print('{title:{fill}{align}100}'.format(title='SHAPE OBJECTS (.SHP FILE)', fill=FILL, align=CENTER))
    print('Reader.shapes() = %s' % type(shapes))
    print('len(Reader.shapes()) = %s' % len(shapes))
    print('Sample(10) iteration through shapes:')
    for s in sample(list(sf.iterShapes()), 10):
        print('    s.shapeType = %s, s.bbox = %s, s.points = %s' % (s.shapeType, s.bbox, s.points))

    # RECORD OBJECTS
    print(SKIP)
    print('{title:{fill}{align}100}'.format(title='RECORD OBJECTS (.DBF FILE)', fill=FILL, align=CENTER))
    print('Reader.records() = %s' % type(records))
    print('len(Reader.records()) = %s' % len(records))
    print('Sample(10) iteration through records:')
    for r in sample(list(sf.iterRecords()), 10):
        print('   r = %s' % r)

    # THE SAME USING FIONA
    print(SKIP)
    print('{title:{fill}{align}100}'.format(title='OPEN BOTH FILES USING FIONA', fill=FILL, align=CENTER))
    shapes = fiona.open(SHP)
    for i, s in enumerate(shapes):
        pprint(s)
        if i > 3:
            break


def fix_checkpoints(checkpoints):
    """
    Type cast the primary key of the checkpoint table (checkpoint_id) into an integer.
    This bug has now been fixed but we keep this function for backward compatibility.
    """

    if checkpoints.index.dtype != 'int64':
        checkpoints.reset_index(inplace=True)
        checkpoint_ids = checkpoints['checkpoint_id'].astype(np.int64, raise_on_error=True)
        checkpoints['checkpoint_id'] = checkpoint_ids
        checkpoints.set_index('checkpoint_id', inplace=True)

    return checkpoints


if __name__ == '__main__':
    print('M5 utilities module:', end=SKIP)
    print('Latest database = %s' % latest_file(DATABASE))
    print('Unique output file: %s' % unique_file('example.unique'))
    check_shapefile()