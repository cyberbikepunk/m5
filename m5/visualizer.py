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
from matplotlib.figure import Figure

from user import User
from settings import PLOT_FONTSIZE, FIGURE_STYLE, OUTPUT_DIR
from settings import FIGURE_SIZE, FIGURE_FONT, DEBUG, FILL
from settings import SHP_FILE, LEAP, MASK_FILE, WORD_SOURCE, WORD_BLACKLIST
from settings import MAX_WORDS, HORIZONTAL_WORDS, BACKGROUND_ALPHA


def _set_plotting_options():
    pd.set_option('display.mpl_style', FIGURE_STYLE)
    plt.rc('font', family=FIGURE_FONT, size=PLOT_FONTSIZE)


def _load_plz():
    """ Load Berlin postal code boundary data from file. """

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


# Do at import time:
_PLZ = _load_plz()
_set_plotting_options()


def _slice_data(df: DataFrame, begin: datetime, end: datetime):
    """ Slice a time window from the pandas dataframe. """
    # Find the indices closest to the window boundaries.
    first = df.index.searchsorted(begin)
    last = df.index.searchsorted(end)
    return df.ix[first:last]


def _make_unique_filepath(filename):
    (base, extension) = splitext(filename)
    stamp = sub(r'[:]|[-]|[_]|[.]|[\s]', '', str(datetime.now()))
    unique = base.ljust(20, FILL) + stamp + extension
    filepath = join(OUTPUT_DIR, unique)
    print('Saved %s' % filepath)
    return filepath


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
        data[['city_tour',
              'distance']].plot(kind='scatter',
                                x='distance',
                                y='city_tour')


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


class CumulativeKm(Chart):
    """ A cummulative timeseries of job distances. """

    def __init__(self):
        super(CumulativeKm, self).__init__()

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
        words = self._assemble_words(data)
        mask = self._build_mask()
        w = WordCloud(stopwords=WORD_BLACKLIST,
                      prefer_horizontal=HORIZONTAL_WORDS,
                      max_words=MAX_WORDS,
                      mask=mask)
        image = w.generate(words)
        self.axes.imshow(image)

    @staticmethod
    def _build_mask():
        original = misc.imread(MASK_FILE)
        flattened = original.sum(axis=2)
        # The flattened image is the reverse of what we want.
        invert_all = vectorize(lambda x: 0 if x > 0 else 1)
        return invert_all(flattened)

    @staticmethod
    def _assemble_words(data):
        word_list = data[WORD_SOURCE].dropna().values
        return whitespace.join(word_list).replace(punctuation, whitespace)


def plz_chloropeth(data):
    """ A chloropeth map of Berlin postal codes using pick-up & drop-off frequencies. """

    postal_codes = data['postal_code'].dropna()
    berlin = postal_codes[(postal_codes > 10100) & (postal_codes < 14200)]
    frequencies = berlin.groupby(postal_codes).count().apply(log)

    records = fiona.open(SHP_FILE)
    codes = [record['properties']['PLZ99_N'] for record in records]
    areas = MultiPolygon([shape(record['geometry']) for record in records])
    plz = dict(zip(codes, areas))

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

    fig = plt.figure(figsize=FIGURE_SIZE)
    ax = fig.add_subplot(111)

    minx, miny, maxx, maxy = records.bounds
    w, h = maxx - minx, maxy - miny
    ax.set_xlim(minx - 0.1 * w, maxx + 0.1 * w)
    ax.set_ylim(miny - 0.1 * h, maxy + 0.1 * h)

    ax.set_aspect(1.7)

    patches = []
    for code, area in plz.items():

        if code not in list(frequencies.index.values):
            frequency = 0
        else:
            frequency = frequencies.loc[code]

        colour = color_map(frequency / normalize)
        patches.append(PolygonPatch(area, fc=colour, ec='#555555', alpha=1., zorder=1))

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


def pickups_n_dropoffs(df):
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


class Dashboard():
    """ A dashboard is a a Matplotlib figure window with subplots. """

    def __init__(self, data: DataFrame, time_window):
        self.data = _slice_data(data, *time_window)
        self.charts = list()
        self.title = str()
        self.figure = Figure()
        self.canvas = None

    def make(self):
        self._configure()
        self._populate()
        self._print()
        self._save()

    def _populate(self):
        for chart, position in self.charts:
            chart().make(self.data, self.figure, position)

    def _configure(self):
        pass

    def _print(self):
        self.figure.show()
        # canvas = FigureCanvas(self.figure)
        # canvas.print_figure(self.title)

    def _save(self):
        pass


class DayDashboard(Dashboard):
    def __init__(self, data, time_window):
        super(DayDashboard, self).__init__(data, time_window)

    def _configure(self):
        self.title = str(self.data.index[0])
        self.charts = [(CumulativeKm, 111)]
        print('Making YearDashboard')


class MonthDashboard(Dashboard):
    def __init__(self, data, time_window):
        super(MonthDashboard, self).__init__(data, time_window)

    def _configure(self):
        self.title = str(self.data.index[0])
        self.charts = [(CumulativeKm, 111)]


class YearDashboard(Dashboard):
    def __init__(self, data, time_window):
        super(YearDashboard, self).__init__(data, time_window)

    def _configure(self):
        self.title = str(self.data.index[0])
        self.charts = [(CumulativeKm, 111)]


def visualize(time_window: tuple, option: str):
    """ Visualize data by day, month or year. """

    assert time_window[0] <= time_window[1], 'Cannot return to the future'

    user = User(username='m-134', password='PASSWORD', db_file='m-134-v2.sqlite')
    data = user.db.joined
    print('Starting data visualization...')

    if option == '-year':
        YearDashboard(data, time_window).make()
    elif option == '-month':
        MonthDashboard(data, time_window).make()
    elif option == '-day':
        DayDashboard(data, time_window).make()


if __name__ == '__main__':
    """ Example """
    win = datetime(2013, 1, 1), datetime(2013, 12, 31, hour=23, minute=59)
    opt = '-year'
    visualize(win, opt)