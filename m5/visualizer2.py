""" A better class-oriented visualization module. """


from re import sub
from geopandas import GeoDataFrame
from matplotlib.figure import Figure
from os.path import splitext, join
from settings import DEBUG, FONT, FONTSIZE, STYLE, FILL, FIGSIZE, OUTPUT, SHP
from pandas import DataFrame, set_option
from datetime import date as Date, datetime
from user import User
from matplotlib.pyplot import rc, figure, show, savefig


def _slice(df: DataFrame, start: Date, stop: Date) -> DataFrame:
    """ Select a time window. """
    first = df.index.searchsorted(start)
    last = df.index.searchsorted(stop)
    return df.ix[first:last]


class Canvas():
    """ A Matplotlib figure window. """

    def __init__(self, title, file):
        self.title = title
        self.file = self._unique(file)

    def prepare(self):
        """ Return a new figure handle. """
        fig = figure(figsize=FIGSIZE, tight_layout=True)
        fig.suptitle(self.title)
        return fig

    def pop(self):
        show(block=True)

    def save(self):
        savefig(self._unique(self.file))

    @staticmethod
    def _unique(file: str) -> str:
        """ Return a unique filepath. """
        (base, extension) = splitext(file)
        stamp = sub(r'[:]|[-]|[_]|[.]|[\s]', '', str(datetime.now()))
        unique = base.ljust(20, FILL) + stamp + extension
        path = join(OUTPUT, unique)
        print('Saved %s' % path)
        return path



def set_plotting_options():
    set_option('display.mpl_style', STYLE)
    rc('font', family=FONT, size=FONTSIZE)


class Plot():
    def __init__(self, data):
        self._figure = None
        self._axes = None
        self.draw = None
        self._xlabel = None
        self.ylabel = None
        self.title = None
        self.placement = None
        self.file = None
        self.aspect_ratio = None

    def define(self):
        pass

    def plot(self):
        pass

    def _set_axes(self, fig: Figure):
        """ Draw the postal code boundaries on a new figure. """
        ax = fig.add_subplot(self.placement)
        ax.set_xlabel(self._xlabel)
        ax.set_ylabel(self.ylabel)
        ax.set_aspect(self.aspect_ratio)
        return ax

    def _draw_plz(self):
        """ Draw the postal code boundaries on a new figure. """
        shp = self._read_plz()
        plz = shp['geometry']
        plz.plot(alpha=.1, axes=self._axes)

    @staticmethod
    def _read_plz() -> GeoDataFrame:
        """ Read in Berlin postal code data from the shapely file. """
        shp = GeoDataFrame.from_file(SHP)
        shp.set_index('PLZ99', inplace=True)
        return shp.sort()




class MonthlyIncome(Plot):
    def __init__(self, data):
        super(MonthlyIncome, self).__init__(data)

    def
        self._figure = None
        self._axes = None
        self.draw = None
        self.xlabel = None
        self.ylabel = None
        self.title = None
        self.placement = None
        self.file = None

        self.draw()


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