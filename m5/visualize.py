from m5.utilities import unique_file
import pandas as pd
import numpy as np
import fiona
import matplotlib.pyplot as plt

from matplotlib.collections import PatchCollection
from descartes import PolygonPatch
from shapely.geometry import MultiPolygon, shape
from geopandas import GeoDataFrame
from matplotlib.colors import LogNorm
from math import log

from m5.settings import SHP, DEBUG, FORMAT, FONTSIZE, SKIP
from m5.user import User


class Visualizer():
    """ Does all the geographic visualization stuff. """

    def __init__(self, db: pd.DataFrame):
        """ Duplicate the database and set plotting options. """
        # FIXME: Visualizer and Analyzer constructors duplicate code

        self.db = db

        # Graphs look much better with this setting.
        pd.set_option('display.mpl_style', 'default')

        # There are plenty of zeros in the database because the model forces
        # zero as the default for certain missing values. This is now fixed,
        # but the following statement is kept for backward compatibility.
        self.db['orders'].replace(0, np.nan, inplace=True)

        # Matplotlib can't find the default
        # font, so we give it another one.
        plt.rc('font', family='Droid Sans', size=FONTSIZE)

    @staticmethod
    def read_plz():
        """ Read in Berlin postal code data from the shapely file. """

        # To read in a GeoDataFrame from a file, geopandas will actually assume that
        # the following 3 files live in the same folder: SHP.shp, SHP.dbf and SHP.shx.
        plz = GeoDataFrame.from_file(SHP)
        plz.set_index('PLZ99', inplace=True)
        plz.sort()

        if DEBUG:
            # Print the GeoDataFrame
            print('{begin}{title:{fill}{align}100}'.format(title=SHP, **FORMAT))
            pd.set_option('expand_frame_repr', False)
            print(plz, end=SKIP)
            print(plz.describe(), end=SKIP)
            print(plz.info(), end=SKIP)

            # Plot the GeoDataFrame
            plz.plot()
            plt.show(block=True)

    def plz_chloropeth(self):
        """ A chloropeth map of Berlin postal codes using pick-up & drop-off frequencies. """

        # Grab Berlin postal codes.
        postal_codes = self.db['all']['postal_code'].dropna()
        berlin = postal_codes[(postal_codes > 10100) & (postal_codes < 14200)]

        # Calculate the number of points inside each postal area.
        frequencies = berlin.groupby(postal_codes).count().apply(log)

        # Load the Berlin postal code area data from file.
        records = fiona.open(SHP)
        codes = [record['properties']['PLZ99_N'] for record in records]
        areas = MultiPolygon([shape(record['geometry']) for record in records])
        plz = dict(zip(codes, areas))

        # Prepare the colormap
        color_map = plt.get_cmap('gist_heat')
        normalize = max(frequencies)

        if DEBUG:
            print('Frequencies = {end}'.format(end=SKIP), frequencies, end=SKIP)
            print('Frequencies.loc[13187] = %s' % frequencies.loc[10115])
            print('Areas = %s' % areas)
            print('Codes = %s' % codes)
            print('Zipped(codes, areas) = %s' % plz)
            print('Lowest and highest postal code = (%s, %s)' % (min(codes), max(codes)))
            print('Color map = %s' % color_map)
            print('Number of colors = %s' % normalize, end=SKIP)

        # Create the figure
        fig = plt.figure()
        ax = fig.add_subplot(111)

        # Set the bounds on the axes
        minx, miny, maxx, maxy = records.bounds
        w, h = maxx - minx, maxy - miny
        ax.set_xlim(minx - 0.1 * w, maxx + 0.1 * w)
        ax.set_ylim(miny - 0.1 * h, maxy + 0.1 * h)
        ax.set_aspect(1.7)

        # Create a collection of patches.
        patches = []
        for code, area in plz.items():

            # We haven't everywhere in Berlin...
            if code not in list(frequencies.index.values):
                frequency = 0
            else:
                frequency = frequencies.loc[code]

            # Put the colored patch on the map!
            colour = color_map(frequency / normalize)
            patches.append(PolygonPatch(area, fc=colour, ec='#555555', alpha=1., zorder=1))

        # Add the collection to the figure
        ax.add_collection(PatchCollection(patches, match_original=True))
        ax.set_xticks([])
        ax.set_yticks([])
        plt.title('pick-up & drop-off')
        plt.savefig(unique_file('plz_map_of_checkins.png'), alpha=True, dpi=300)
        plt.show(block=True)


if __name__ == '__main__':
    u = User('x', 'y')
    v = Visualizer(u.db)
    v.plz_chloropeth()