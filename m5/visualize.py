import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm

from matplotlib.colors import Normalize
from matplotlib.collections import PatchCollection
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon
from shapely.prepared import prep
from descartes import PolygonPatch
import fiona
from pprint import pprint

from geopandas import GeoDataFrame
from m5.settings import SHP, DEBUG, FORMAT, FONTSIZE, SKIP


class Visualizer():
    """ Does all the geographic visualization stuff. """

    def __init__(self, db: pd.DataFrame):
        """ Duplicate the database and set plotting options. """
        # FIXME: Visualizer and Analyzer constructors duplicate code

        self.db = db

        # Graphs look much better with this setting.
        pd.set_option('display.mpl_style', 'default')

        # There are plenty of zeros in the database because the model
        # forces zero as the default for missing values. This is now fixed,
        # but the following statement is kept for backward compatibility.
        self.db['orders'].replace(0, np.nan, inplace=True)

        # Matplotlib can't find the default
        # font, so we give it another one.
        plt.rc('font', family='Droid Sans', size=FONTSIZE)


    @staticmethod
    def read_plz():
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
        """ A chloropeth map of checkin frequencies. """

        income = self.db['checkins'][['postal_code',
                                    'overnight',
                                    'waiting_time',
                                    'extra_stops',
                                    'fax_confirm']]

        prices = pd.concat([income, income.sum(axis=1), dates], axis=1)
        prices.rename(columns={0: 'total'}, inplace=True)

        timeseries = prices.groupby('date').sum()

    @staticmethod
    def plot_polygon(ax, poly, facecolor='red', edgecolor='black', alpha=0.5):
        """ Plot a single Polygon geometry """
        from descartes.patch import PolygonPatch
        a = np.asarray(poly.exterior)
        # without Descartes, we could make a Patch of exterior
        ax.add_patch(PolygonPatch(poly, facecolor=facecolor, alpha=alpha))
        ax.plot(a[:, 0], a[:, 1], color=edgecolor)
        for p in poly.interiors:
            x, y = zip(*p.coords)
            ax.plot(x, y, color=edgecolor)


if __name__ == '__main__':
    read_shapely()