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

from user import User
from settings import FONTSIZE, STYLE, OUTPUT, FIGSIZE, FONT, DEBUG, FILL, CENTER, PLZ_ALPHA
from settings import SHP, LEAP, MASK, WORDS, BLACKLIST, MAXWORDS, PROPORTION


def _set_plotting_options():
    """ Make the plots reasonnably pretty. """
    pd.set_option('display.mpl_style', STYLE)
    plt.rc('font', family=FONT, size=FONTSIZE)


def _load_plz():
    """ Load postal code polygon data from file. """
    # Although we specify only one file path,
    # it seems that geopandas assumes that
    # the following 3 files live in the same
    # folder: SHP.shp, SHP.dbf and SHP.shx.
    plz = GeoDataFrame.from_file(SHP)
    plz.set_index('PLZ99', inplace=True)
    plz.sort()
    if DEBUG:
        print(plz, end=LEAP)
        print(plz.describe(), end=LEAP)
        print(plz.info(), end=LEAP)
    return plz


_PLZ = _load_plz()
_set_plotting_options()


class Chart():
    """ A Chart is a subplot inside a matplotlib figure. """

    def __init__(self, data, figure, position):
        # See child classes.
        self.axes = None
        self.grid = None
        self.aspect_ratio = None
        self.specs = None
        self.x_minor_formatter = None

        self._insert(figure, position)
        self._plot(data)

    @property
    def title(self):
        return None

    @property
    def xlabel(self):
        return None

    @property
    def ylabel(self):
        return None

    def _insert(self, figure, position):
        """ Place a subplot where we want. """
        self.axes = figure.add_subplot(position)
        self.axes.set_title(self.title)
        self.axes.grid(self.grid)
        self.axes.set_xlabel(self.xlabel)
        self.axes.set_ylabel(self.ylabel)

    def _plot(self, data):
        """ Process and plot the data. """
        pass

    def _draw_postal_boundaries(self) -> GeoDataFrame:
        """ Add postal code polygons to the plot. """
        _PLZ['geometry'].plot(alpha=PLZ_ALPHA, axes=self.axes)

    def _format_x_minor_ticks(self):
        self.axes.xaxis.set_minor_formatter(self.x_minor_formatter)


class PriceHistogram(Chart):
    """ A histogram of job prices stacked by type. """

    def __init__(self):
        super(PriceHistogram, self).__init__(data, figure, position)
        self.ylabel('Number of jobs')
        self.xlabel('Job price (€)')

    def _plot(self, data):
        prices = data[['city_tour',
                       'overnight',
                       'waiting_time',
                       'extra_stops',
                       'fax_confirm']]

        axes = prices.plot(kind='hist',
                         stacked=True,
                         bins=40,
                         xlim=(1, 30),
                         figsize=FIGSIZE,
                         title='Job price distribution',
                         fontsize=FONTSIZE)


def price_vs_km():
    """ A scatter plot of the wage per kilometer. """

    scatter = df[['city_tour', 'distance']]

    ax = scatter.plot(kind='scatter',
                      x='distance',
                      y='city_tour',
                      figsize=FIGSIZE,
                      title='Wage vs distance',
                      fontsize=FONTSIZE)

    ax.set_ylabel('Job distance (km)')
    ax.set_ylabel('Job price (€)')
    plt.tight_layout()

    _make_image('price_vs_km.png')


class MonthlyIncome(Chart):
    """ A timeseries plot of the monthly income. """

    def __init__(self, data, figure, position):
        super(MonthlyIncome, self).__init__(data, figure, position)
        self.arguments = {'kind': 'bar', 'stacked': True}

    def _plot(self, data):
        income = data[['city_tour', 'overnight', 'fax_return', 'waiting_time', 'extra_stop']]
        self.repair_prices(income)
        monthly = income.resample('M', how='sum')
        self.axes = monthly.plot(self.arguments)

    @property
    def x_minor_formatter(self):
        return DateFormatter('%y')

    @staticmethod
    def repair_prices(prices):
        """ Correct the price information. """
        # There are lots of zeros in the prices because the database model was
        # forcing zero as the default for missing values. This is now fixed.
        return prices.replace(0, np.nan, inplace=True)


class Terminal():
    """ Print basic statistics in the terminal. """

    def __init__(self):
        pass

    @staticmethod
    def _print_header(title):
        """ A wide horizontal section title. """
        print('{begin}{title:{fill}{align}100}{end}'.format(title=title, fill=FILL, align=CENTER, begin=LEAP, end=LEAP))


class Dashboard():
    """ A dashboard is a collection of subplots in a Matplotlib figure window. """

    def __init__(self, data: DataFrame, time_window):
        self.positions = set()

        self.data = self._slice(data, *time_window)
        self.figure = Figure()

        for position in self.positions:
            Chart(self.data, self.figure, position)

        self.canvas = FigureCanvasAgg(self.figure)
        self.canvas.print_figure(self.title)
        self._save()

    def _save(self):
        pass

    @property
    def title(self):
        return None

    @staticmethod
    def _slice(df: DataFrame, begin, end):
        """ Slice a time window from the database. """
        # Find the indices closest to the window boundaries
        first = df.index.searchsorted(begin)
        last = df.index.searchsorted(end)
        return df.ix[first:last]

    @staticmethod
    def _unique(path: str, file: str) -> str:
        """ Return a unique filepath. """
        (base, extension) = splitext(file)
        stamp = sub(r'[:]|[-]|[_]|[.]|[\s]', '', str(datetime.now()))
        unique = base.ljust(20, FILL) + stamp + extension
        path = join(path, unique)
        print('Saved %s' % path)
        return path


class DayDashboard(Dashboard):

    def __init__(self, data: DataFrame, time_window):
        super(Dashboard, self).__init__(data, time_window)

    @property
    def title(self):
        pass


def cumulative_km():
    """ A cummulative timeseries of job distances. """

    km = df[['distance']]
    accumulated = km.resample('D', how='sum').replace(np.nan, 0).cumsum()

    x = accumulated.index.values
    y = accumulated.values

    with plt.style.context('fivethirtyeight'):
        fig = plt.figure(figsize=FIGSIZE)
        ax = fig.add_subplot(111)

        ax.plot(x, y, 'r')
        ax.set_xlabel('time')
        ax.set_ylabel('km')
        ax.set_title('cummulative kms')

    _make_image('cummulative_km.png')

def streetcloud():
    """ A wordcloud of street names using Andreas Müller's code. """

    assert isfile(MASK), 'Could not find {file} for the mask.'.format(file=MASK)

    word_series = df[WORDS].dropna()
    word_list = word_series.values
    word_string = whitespace.join(word_list).replace(punctuation, whitespace)

    original = misc.imread(MASK)
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

    w = WordCloud(stopwords=BLACKLIST,
                  max_words=MAXWORDS,
                  prefer_horizontal=PROPORTION,
                  mask=mask)

    image = w.generate(word_string)

    plt.imshow(image)
    plt.axis("off")
    _make_image('wordcloud.png')

def plz_chloropeth():
    """ A chloropeth map of Berlin postal codes using pick-up & drop-off frequencies. """

    # Grab Berlin postal codes.
    postal_codes = df['postal_code'].dropna()
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
        _print_header('Chloropeth debug info...')
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

    _make_image('plz_checkin_map.png')

def daily_income():
    """ A timeseries plot of the daily income. """

    db = df.reset_index()
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

    fig = plt.figure(figsize=FIGSIZE)
    ax = fig.add_subplot(111)

    ax.vlines(total.index.values, 0, total.values)
    ax.set_xlabel('Dates')
    ax.set_ylabel('Income (€)')
    ax.set_title('Daily income')
    ax.axhline(mean, color='k')
    plt.tight_layout()

    _make_image('daily_income.png')

def pickups_n_dropoffs():
    """ Spatial map of checkpoints (split pick-ups and drop-offs). """

    pickups = df[(df['city'] == 'Berlin') & (df['purpose'] == 'pickup')]
    dropoffs = df[(df['city'] == 'Berlin') & (df['purpose'] == 'dropoff')]

    if DEBUG:
        _print_header('Pickups...')
        print(pickups)
        _print_header('Dropoffs...')
        print(dropoffs)

    ax = _make_background()
    ax.plot(pickups['lon'], pickups['lat'], 'k.', markersize=12)
    ax.plot(dropoffs['lon'], dropoffs['lat'], 'b.', markersize=12, alpha=0.5)

    plt.title('Pick-ups (black) and drop-offs (blue)')
    _make_image('lat_lon.png')


def visualize(time_window: tuple, option: str):
    """ Visualize data by day, month or year. """

    assert time_window[0] <= time_window[1], 'Cannot return to the future'
    print('Starting data visualization...')

    user = User(username='m-134', password='PASSWORD', db_file='m-134-v2.sqlite')
    dashboard = Dashboard(user.db.joined, time_window)

    if option == '-year':
        dashboard.subplot(monthly_income, 221)
        dashboard.subplot(price_histogram, 222)
        dashboard.subplot(cumulative_km, 223)
        dashboard.subplot(price_vs_km, 224)

    elif option == '-month':
        dashboard.subplot(daily_income, 221)
        dashboard.subplot(plz_chloropeth, 222)
        dashboard.subplot(streetcloud, 223)

    elif option == '-day':
        dashboard.subplot(pickups_n_dropoffs, 221)

if __name__ == '__main__':
    """ Build an example dashboard. """
    option_ = '-year'
    time_window_ = datetime(2013, 1, 1), datetime(2013, 12, 31, hour=23, minute=59)
    visualize(time_window_, option_)