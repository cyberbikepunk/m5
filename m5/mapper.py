""" Maps are made here. """

import pandas as pd
import fiona
import matplotlib.pyplot as plt

from matplotlib.collections import PatchCollection
from descartes import PolygonPatch
from shapely.geometry import MultiPolygon, shape
from geopandas import GeoDataFrame
from math import log

from settings import SHP, DEBUG, FIGSIZE, LEAP
from user import User
from utilities import Visualizor, make_image, print_header


class Mapper(Visualizor):
    """ Does all the geographic visualization stuff. """

    def __init__(self, db: pd.DataFrame):
        super(Mapper, self).__init__(db)

    # def day_arrows(self, day):
    #
    #     one_day = self.db['all'][(self.db['all']['city'] == 'Berlin') & (self.db['all']['date'] == day)]
    #     print(one_day)
    #     pickups = one_day[one_day['purpose'] == 'pickup']
    #     dropoffs = one_day[one_day['purpose'] == 'dropoff']
    #
    #     print(list(zip(pickups, dropoffs)))
    #     ax.arrow(0, 0, 0.5, 0.5, head_width=0.05, head_length=0.1, fc='k', ec='k')

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
            print_header(SHP)
            print(plz, end=LEAP)
            print(plz.describe(), end=LEAP)
            print(plz.info(), end=LEAP)

        return plz

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
        color_map = plt.get_cmap('Reds')
        normalize = max(frequencies)

        if DEBUG:
            print_header('Chloropeth debug info')
            print('Frequencies = {end}'.format(end=LEAP), frequencies, end=LEAP)
            print('Frequencies.loc[13187] = %s' % frequencies.loc[10115])
            print('Areas = %s' % areas)
            print('Codes = %s' % codes)
            print('Zipped(codes, areas) = %s' % plz)
            print('Lowest and highest postal code = (%s, %s)' % (min(codes), max(codes)))
            print('Color map = %s' % color_map)
            print('Number of colors = %s' % normalize, end=LEAP)

        # Create the figure
        fig = plt.figure(figsize=FIGSIZE)
        ax = fig.add_subplot(111)

        # Set the bounds on the axes
        minx, miny, maxx, maxy = records.bounds
        w, h = maxx - minx, maxy - miny
        ax.set_xlim(minx - 0.1 * w, maxx + 0.1 * w)
        ax.set_ylim(miny - 0.1 * h, maxy + 0.1 * h)
        # This is dirty:
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
        plt.title('Heat-map of checkpoints')

        make_image('plz_checkin_map.png')

    def pickups_n_dropoffs(self):
        """ Spatial map of checkpoints (split pick-ups and drop-offs). """

        # Pop a figure with a back-drop
        ax = self.make_background()

        # Select pick-ups and drop-offs in Berlin
        pickups = self.db['all'][(self.db['all']['city'] == 'Berlin') & (self.db['all']['purpose'] == 'pickup')]
        dropoffs = self.db['all'][(self.db['all']['city'] == 'Berlin') & (self.db['all']['purpose'] == 'dropoff')]

        if DEBUG:
            print_header('Pickups')
            print(pickups)
            print_header('Dropoffs')
            print(dropoffs)

        ax.plot(pickups['lon'], pickups['lat'], 'k.', markersize=12)
        ax.plot(dropoffs['lon'], dropoffs['lat'], 'b.', markersize=12, alpha=0.5)

        plt.title('Pick-ups (black) and drop-offs (blue)')
        make_image('lat_lon.png')

    def make_background(self):
        """ Map the postal code boundary in the background. """

        fig = plt.figure(figsize=FIGSIZE)
        ax = fig.add_subplot(111)
        ax.set_xlabel('lon')
        ax.set_ylabel('lat')
        ax.set_aspect(1.5)

        # The postal code background.
        shp = self.read_plz()
        plz = shp['geometry']
        plz.plot(alpha=.1, axes=ax)

        return ax

if __name__ == '__main__':
    u = User(db_file='m-134-v2.sqlite')
    v = Mapper(u.db)
    v.pickups_n_dropoffs()
    v.plz_chloropeth()
