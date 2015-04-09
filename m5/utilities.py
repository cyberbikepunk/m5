""" Miscellaneous utility classes decorators and functions """


import fiona
import shapefile
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from pprint import pprint
from collections import namedtuple
from datetime import datetime
from os.path import splitext, join, getctime
from os import listdir
from glob import iglob
from re import sub
from random import sample

from m5.settings import FILL, OUTPUT, DATABASE, LEAP, CENTER, DBF, SHP, FONTSIZE, POP, FIGSIZE


# --------------------- CLASSES


class Visualizor():
    """ Parent class for the Plotter and Mapper classes. """

    def __init__(self, db: pd.DataFrame):
        """ Copy the database and set plotting options. """

        self.db = db

        # Graphs look much better with this setting.
        pd.set_option('display.mpl_style', 'default')

        # There are plenty of zeros in the database because the model
        # forces zero as the default for missing values. This is now fixed,
        # but the following statement is kept for backward compatibility.
        # self.db['orders'].replace(0, np.nan, inplace=True)

        # Matplotlib can't find the default
        # font, so we give it another one.
        plt.rc('font', family='Droid Sans', size=FONTSIZE)

    @staticmethod
    def prepare_image(title):
        fig = plt.figure(figsize=FIGSIZE, tight_layout=True)
        fig.suptitle(title)
        return fig

    @staticmethod
    def make_image(file):
        plt.savefig(unique_file(OUTPUT, file))
        if POP:
            plt.show(block=True)

    def _totals(self):
        totals = dict()
        for table in self.db.keys():
            totals[table] = self.db[table].shape[0]
            self.db[table].reset_index(inplace=True)
        return totals



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


def make_image(name):

    plt.savefig(unique_file(OUTPUT, name))
    if POP:
        plt.show(block=True)


def unique_file(path, file: str) -> str:
    """ Return a unique path in the output folder. """

    (base, extension) = splitext(file)
    stamp = sub(r'[:]|[-]|[_]|[.]|[\s]', '', str(datetime.now()))
    unique = base.ljust(20, FILL) + stamp + extension
    path = join(path, unique)

    print('Saved %s' % path)

    return path


def latest_file(folder: str):
    """ Return the most recent file inside the folder. """

    if listdir(folder):
        file = max(iglob(join(folder, '*.sqlite')), key=getctime)
    else:
        file = 'database.sqlite'
    print('Selected {folder}/{file}'.format(folder=folder, file=file))

    return file


def print_header(title):
    """ A wide horizontal section title. """
    print('{begin}{title:{fill}{align}100}{end}'.format(title=title, fill=FILL, align=CENTER, begin=LEAP, end=LEAP))


def check_shapefile():
    """ Examine the inner contents of a shapefile with shapely and fiona. """

    # OPEN THE FILES WITH SHAPELY
    shp = open(SHP, 'rb')
    dbf = open(DBF, 'rb')
    sf = shapefile.Reader(shp=shp, dbf=dbf)

    shapes = sf.shapes()
    records = sf.records()

    # READER OBJECT
    print(LEAP)
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
    print(LEAP)
    print('{title:{fill}{align}100}'.format(title='SHAPE OBJECTS (.SHP FILE)', fill=FILL, align=CENTER))
    print('Reader.shapes() = %s' % type(shapes))
    print('len(Reader.shapes()) = %s' % len(shapes))
    print('Sample(10) iteration through shapes:')
    for s in sample(list(sf.iterShapes()), 10):
        print('    s.shapeType = %s, s.bbox = %s, s.points = %s' % (s.shapeType, s.bbox, s.points))

    # RECORD OBJECTS
    print(LEAP)
    print('{title:{fill}{align}100}'.format(title='RECORD OBJECTS (.DBF FILE)', fill=FILL, align=CENTER))
    print('Reader.records() = %s' % type(records))
    print('len(Reader.records()) = %s' % len(records))
    print('Sample(10) iteration through records:')
    for r in sample(list(sf.iterRecords()), 10):
        print('   r = %s' % r)

    # DO THE SAME WITH FIONA
    print(LEAP)
    print('{title:{fill}{align}100}'.format(title='OPEN BOTH FILES USING FIONA', fill=FILL, align=CENTER))
    shapes = fiona.open(SHP)
    for i, s in enumerate(shapes):
        pprint(s)
        if i > 3:
            break


def fix_checkpoints(checkpoints):
    """
    Type cast the primary key of the checkpoint table (checkpoint_id) into an integer.
    This bug has now been fixed but we keep this function for backwards compatibility.
    """

    if checkpoints.index.dtype != 'int64':
        checkpoints.reset_index(inplace=True)
        checkpoint_ids = checkpoints['checkpoint_id'].astype(np.int64, raise_on_error=True)
        checkpoints['checkpoint_id'] = checkpoint_ids
        checkpoints.set_index('checkpoint_id', inplace=True)

    return checkpoints


if __name__ == '__main__':
    print('M5 utilities module:', end=LEAP)
    print('Latest database = %s' % latest_file(DATABASE))
    print('Unique output file: %s' % unique_file(OUTPUT, 'example.unique'))
    check_shapefile()