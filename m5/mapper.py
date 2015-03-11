from m5.utilities import unique_file, make_graph
import pandas as pd
import fiona
import matplotlib.pyplot as plt

from matplotlib.collections import PatchCollection
from descartes import PolygonPatch
from shapely.geometry import MultiPolygon, shape
from geopandas import GeoDataFrame
from math import log

from m5.settings import SHP, DEBUG, FILL, CENTER, LEAP
from m5.user import User
from m5.utilities import Grapher


class Mapper(Grapher):
    """ Does all the geographic visualization stuff. """

    def __init__(self, db: pd.DataFrame):
        super(Mapper, self).__init__(db)

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
            pd.set_option('expand_frame_repr', False)
            print(LEAP)
            print('{title:{fill}{align}100}'.format(title=SHP, fill=FILL, align=CENTER), end=LEAP)
            print(plz, end=LEAP)
            print(plz.describe(), end=LEAP)
            print(plz.info(), end=LEAP)

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
            print('Frequencies = {end}'.format(end=LEAP), frequencies, end=LEAP)
            print('Frequencies.loc[13187] = %s' % frequencies.loc[10115])
            print('Areas = %s' % areas)
            print('Codes = %s' % codes)
            print('Zipped(codes, areas) = %s' % plz)
            print('Lowest and highest postal code = (%s, %s)' % (min(codes), max(codes)))
            print('Color map = %s' % color_map)
            print('Number of colors = %s' % normalize, end=LEAP)

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

            # Make a collection of patches
            colour = color_map(frequency / normalize)
            patches.append(PolygonPatch(area, fc=colour, ec='#555555', alpha=1., zorder=1))

        # Add the collection to the figure
        ax.add_collection(PatchCollection(patches, match_original=True))
        ax.set_xticks([])
        ax.set_yticks([])
        plt.title('pick-up & drop-off')

        make_graph('plz_checkin_map.png')


if __name__ == '__main__':
    u = User('x', 'y')
    v = Mapper(u.db)
    v.plz_chloropeth()