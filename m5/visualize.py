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
from m5.settings import SHP, DEBUG, FORMAT, SKIP


def read_shapely():
    # To extract a GeoDataFrame from file, geopandas will actually assume that
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


if __name__ == '__main__':
    read_shapely()