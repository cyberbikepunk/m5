""" All the visualization happens here. """


import numpy as np
import pandas as pd
import fiona
import matplotlib.pyplot as plt

from numpy import vectorize
from os.path import isfile, join, splitext
from geopandas import GeoDataFrame
from matplotlib.collections import PatchCollection
from descartes import PolygonPatch
from pandas.util.testing import DataFrame
from shapely.geometry import MultiPolygon, shape
from matplotlib.dates import DateFormatter
from math import log
from wordcloud import WordCloud
from string import punctuation, whitespace
from scipy import misc
from re import sub
from datetime import datetime
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from collections import namedtuple

from user import User
from settings import PLOT_FONTSIZE, FIGURE_STYLE, OUTPUT_DIR
from settings import FIGURE_SIZE, FIGURE_FONT, DEBUG, FILL, CENTER
from settings import SHP_FILE, LEAP, MASK_FILE, WORD_SOURCE, WORD_BLACKLIST
from settings import MAX_WORDS, HORIZONTAL_WORDS, BACKGROUND_ALPHA


# Charts are subplots on a matplotlib figure.
Charts = namedtuple('Charts', ['type', 'position'])


def _set_plotting_options():
    """ Make the plots reasonnably pretty. """
    pd.set_option('display.mpl_style', FIGURE_STYLE)
    plt.rc('font', family=FIGURE_FONT, size=PLOT_FONTSIZE)


def _load_plz():
    """ Load postal code boundary data from file. """

    # Although we specify only one file path,
    # it seems that geopandas assumes that
    # the following 3 files live in the same
    # folder: SHP.shp, SHP.dbf and SHP.shx.
    plz = GeoDataFrame.from_file(SHP_FILE)
    plz.set_index('PLZ99', inplace=True)
    plz.sort()

    if DEBUG:
        print(plz, end=LEAP)
        print(plz.describe(), end=LEAP)
        print(plz.info(), end=LEAP)

    return plz


# Execute at import time.
_PLZ = _load_plz()
_set_plotting_options()


class Chart():
    """ A Chart is a subplot inside a matplotlib figure. """

    def __init__(self):
        self.axes = None
        self.grid = False
        self.title = str()
        self.xlabel = str()
        self.ylabel = str()
        self.aspect_ratio = None

    def make(self, data: DataFrame, figure: Figure, position: tuple):
        """ Create one subplot. """
        self._configure()
        self._add(figure, position)
        self._draw(data)

    def _configure(self):
        pass

    def _add(self, figure: Figure, position: tuple):
        """ Add the subplot and make it right. """
        self.axes = figure.add_subplot(position)
        self.axes.set_title(self.title)
        self.axes.grid(self.grid)
        self.axes.set_xlabel(self.xlabel)
        self.axes.set_ylabel(self.ylabel)

    def _draw(self, data):
        pass

    def _draw_postal_boundaries(self):
        """ Add postal code boundaries as a backdrop. """
        _PLZ['geometry'].plot(alpha=BACKGROUND_ALPHA, axes=self.axes)

    @staticmethod
    def _header(title):
        """ A wide horizontal section title for the terminal. """
        return '{pad}{title:{fill}{align}100}{pad}'.format(title=title,
                                                           fill=FILL,
                                                           align=CENTER,
                                                           pad=LEAP)


class PriceHistogram(Chart):
    """ A histogram of job prices stacked by type. """

    def __init__(self):
        super(PriceHistogram, self).__init__()

    def _configure(self):
        self.title = 'Job'
        self.xlabel = 'Job price (€)'
        self.ylabel = 'Number of jobs'

    def _draw(self, data):
        data[['city_tour',
              'overnight',
              'waiting_time',
              'extra_stops',
              'fax_confirm']].plot(kind='hist',
                                   stacked=True,
                                   bins=self._bins,
                                   xlim=self._xlimits,
                                   title=self.title,
                                   axes=self.axes)

    @property
    def _xlimits(self):
        return 1, 30

    @property
    def _bins(self):
        return 40


class PriceVsKm(Chart):
    """ A scatter plot of the wage per kilometer. """

    def __init__(self):
        super(PriceVsKm, self).__init__()

    def _configure(self):
        self.title = 'Wage vs distance'
        self.ylabel = 'Job distance (km)'
        self.xlabel = 'Job price (€)'

    def _draw(self, data):
        data[['city_tour', 'distance']].plot(kind='scatter', x='distance', y='city_tour')


class MonthlyIncome(Chart):
    """ A timeseries plot of the monthly income. """

    def __init__(self):
        super(MonthlyIncome, self).__init__()

    def _draw(self, data):
        self.axes = data[['city_tour',
                          'overnight',
                          'fax_return',
                          'waiting_time',
                          'extra_stop']].replace(np.nan, 0).resample('M', how='sum').plot(kind='bar',
                                                                                          stacked=True)
        self.axes.xaxis.set_minor_formatter(DateFormatter('%y'))


class Dashboard():
    """ A dashboard is a a Matplotlib figure window with subplots. """

    def __init__(self, data: DataFrame, time_window):
        self.data = self._slice_data(data, *time_window)
        self.charts = dict()
        self.title = str()
        self.figure = Figure()
        self.canvas = None

    def make(self):
        self._configure()
        self._populate()
        self._print()
        self._save()

    def _populate(self):
        for chart_type, chart_position in self.charts.items():
            chart_type.make(self.data, self.figure, chart_position)

    def _configure(self):
        pass

    def _print(self):
        canvas = FigureCanvasAgg(self.figure)
        canvas.print_figure(self.title)

    def _save(self):
        pass

    @staticmethod
    def _slice_data(df: DataFrame, begin, end):
        """ Slice a time window from the pandas dataframe. """
        # Find the indices closest to the window boundaries
        first = df.index.searchsorted(begin)
        last = df.index.searchsorted(end)
        return df.ix[first:last]

    @staticmethod
    def _create_unique(filename: str) -> str:
        """ Return a unique filepath inside the output folder. """
        (base, extension) = splitext(filename)
        stamp = sub(r'[:]|[-]|[_]|[.]|[\s]', '', str(datetime.now()))
        unique = base.ljust(20, FILL) + stamp + extension
        path = join(OUTPUT_DIR, unique)
        print('Saved %s' % path)
        return path


class DayPanel(Dashboard):
    def __init__(self, data: DataFrame, time_window):
        super(DayPanel, self).__init__(data, time_window)

    def _configure(self):
        self.title = str(self.data.index[0])
        self.charts = Charts('CumulativeKm', [(1, 1, 1)])


class MonthPanel(Dashboard):
    def __init__(self, data: DataFrame, time_window):
        super(MonthPanel, self).__init__(data, time_window)

    def _configure(self):
        self.title = str(self.data.index[0])
        self.charts = Charts('CumulativeKm', [(1, 1, 1)])


class YearPanel(Dashboard):
    def __init__(self, data: DataFrame, time_window):
        super(YearPanel, self).__init__(data, time_window)

    def _configure(self):
        self.title = str(self.data.index[0])
        self.charts = Charts('CumulativeKm', [(1, 1, 1)])


class CumulativeKm(Chart):
    """ A cummulative timeseries of job distances. """

    def __init__(self):
        super(Chart, self).__init__(d)

    def _configure(self):
        self.xlabel = 'Time'
        self.ylabel = 'Distance (km)'
        self.title = 'Cummulative distance'

    def _draw(self, data):
        accumulated = data[['distance']].resample('D', how='sum').replace(np.nan, 0).cumsum()
        self.axes.plot(accumulated.index.values, accumulated.values, 'r')


class StreetCloud(Chart):
    """ A wordcloud of street names using Andreas Müller's code on GitHub. """

    def __init__(self):
        assert isfile(MASK_FILE), 'Could not find {file} for the mask.'.format(file=MASK_FILE)
        super(StreetCloud, self).__init__()

    def _draw(self, data):
        # Build the text sample
        word_series = data[WORD_SOURCE].dropna()
        word_list = word_series.values
        word_string = whitespace.join(word_list).replace(punctuation, whitespace)

        # Build the cloud mask
        original = misc.imread(MASK_FILE)
        flattened = original.sum(axis=2)

        if DEBUG:
            print(flattened.dtype)
            print(flattened.shape)
            print(flattened.max())
            print(flattened.min())

        # With this particular image, the resulting
        # mask is the exact reverse of what I want.
        invert_all = vectorize(lambda x: 0 if x > 0 else 1)
        mask = invert_all(flattened)

        w = WordCloud(stopwords=WORD_BLACKLIST,
                      max_words=MAX_WORDS,
                      prefer_horizontal=HORIZONTAL_WORDS,
                      mask=mask)

        image = w.generate(word_string)
        self.axes.imshow(image)


def plz_chloropeth(data):
    """ A chloropeth map of Berlin postal codes using pick-up & drop-off frequencies. """

    # Grab Berlin postal codes.
    postal_codes = data['postal_code'].dropna()
    berlin = postal_codes[(postal_codes > 10100) & (postal_codes < 14200)]

    # Calculate the number of points inside each postal area.
    frequencies = berlin.groupby(postal_codes).count().apply(log)

    # Load the Berlin postal code area data from file.
    records = fiona.open(SHP_FILE)
    codes = [record['properties']['PLZ99_N'] for record in records]
    areas = MultiPolygon([shape(record['geometry']) for record in records])
    plz = dict(zip(codes, areas))

    # Prepare the colormap
    color_map = plt.get_cmap('Reds')
    normalize = max(frequencies)

    if DEBUG:
        print('Chloropeth debug info...')
        print('Frequencies = {end}'.format(end=LEAP), frequencies, end=LEAP)
        print('Frequencies.loc[13187] = %s' % frequencies.loc[10115])
        print('Areas = %s' % areas)
        print('Codes = %s' % codes)
        print('Zipped(codes, areas) = %s' % plz)
        print('Lowest and highest postal code = (%s, %s)' % (min(codes), max(codes)))
        print('Color map = %s' % color_map)
        print('Number of colors = %s' % normalize, end=LEAP)

    # Create the figure
    fig = plt.figure(figsize=FIGURE_SIZE)
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


def daily_income(data):
    """ A timeseries plot of the daily income. """

    db = data.reset_index()
    dates = db['date']
    income = db[['city_tour',
                 'overnight',
                 'waiting_time',
                 'extra_stops',
                 'fax_confirm']]

    prices = pd.concat([income, income.sum(axis=1), dates], axis=1)
    prices.rename(columns={0: 'total'}, inplace=True)

    timeseries = prices.groupby('date').sum()
    total = timeseries['total']
    mean = total.mean()

    fig = plt.figure(figsize=FIGURE_SIZE)
    ax = fig.add_subplot(111)

    ax.vlines(total.index.values, 0, total.values)
    ax.set_xlabel('Dates')
    ax.set_ylabel('Income (€)')
    ax.set_title('Daily income')
    ax.axhline(mean, color='k')
    plt.tight_layout()


def pickups_n_dropoffs():
    """ Spatial map of checkpoints (split pick-ups and drop-offs). """

    pickups = df[(df['city'] == 'Berlin') & (df['purpose'] == 'pickup')]
    dropoffs = df[(df['city'] == 'Berlin') & (df['purpose'] == 'dropoff')]

    if DEBUG:
        print('Pickups...')
        print(pickups)
        print('Dropoffs...')
        print(dropoffs)

    ax = None
    ax.plot(pickups['lon'], pickups['lat'], 'k.', markersize=12)
    ax.plot(dropoffs['lon'], dropoffs['lat'], 'b.', markersize=12, alpha=0.5)

    plt.title('Pick-ups (black) and drop-offs (blue)')


def visualize(time_window: tuple, option: str):
    """ Visualize data by day, month or year. """

    assert time_window[0] <= time_window[1], 'Cannot return to the future'
    print('Starting data visualization...')
    user = User(username='m-134', password='PASSWORD', db_file='m-134-v2.sqlite')

    if option == '-year':
        YearPanel(user.db.joined, time_window)
    elif option == '-month':
        MonthPanel(user.db.joined, time_window)
    elif option == '-day':
        DayPanel(user.db.joined, time_window)


if __name__ == '__main__':
    """ Build an example dashboard. """
    win = datetime(2013, 1, 1), datetime(2013, 12, 31, hour=23, minute=59)
    opt = '-year'
    visualize(win, opt)