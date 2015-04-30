""" A better class-oriented visualization module. """


from re import sub
from geopandas import GeoDataFrame
from matplotlib.figure import Figure
from os.path import join
from settings import DEBUG, FILL, FIGURE_SIZE, OUTPUT_FOLDER, SHP_FILE, BAD
from pandas import DataFrame
from datetime import date, datetime
from user import User


def _slice(df: DataFrame, start: date, stop: date) -> DataFrame:
    first = df.index.searchsorted(start)
    last = df.index.searchsorted(stop)
    return df.ix[first:last]


def _unique_filename(title: str) -> str:
    base, extension = title, 'png'
    stamp = sub(BAD, '', str(datetime.now()))
    unique = base.ljust(20, FILL) + stamp + extension
    return join(OUTPUT_FOLDER, unique)


def _read_plz() -> GeoDataFrame:
    shp = GeoDataFrame.from_file(SHP_FILE)
    shp.set_index('PLZ99', inplace=True)
    plz = shp.sort()
    return plz['geometry']

_PLZ = _read_plz()


class Plot():
    figure = None
    xlabel = None
    ylabel = None
    title = None
    placement = None
    filepath = None

    def __init__(self, data):
        pass

    def plot(self):
        pass


class MonthlyIncome(Plot):
    pass


def visualize(time_window: tuple, option: str):
    """ Visualize data by day, month or year. """

    print('Starting data visualization...')
    u = User(db_file='m-134-v2.sqlite')
    data = _slice(u.df, *time_window)

    if option == '-year':
        fig = Canvas(data)
    elif option == '-month':
        pass
    elif option == '-day':
        pass