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
from shapely.geometry import MultiPolygon, shape
from matplotlib.dates import DateFormatter
from math import log
from wordcloud import WordCloud
from string import punctuation, whitespace
from scipy import misc
from datetime import datetime
from re import sub

from user import User
from settings import FONTSIZE, STYLE, OUTPUT, FIGSIZE, FONT, DEBUG, FILL, CENTER
from settings import SHP, LEAP, MASK, WORDS, BLACKLIST, MAXWORDS, PROPORTION


class Visualizer():
    """ Parent class for the visualization magic. """

    def __init__(self, df: pd.DataFrame, tables: dict, start: datetime, stop: datetime):
        """ Initialize object attributes. """

        self.start = start
        self.stop = stop
        self.df = self._slice(df)
        self.tables = dict

        for name, table in tables.items():
            self.tables[name] = self._slice(table)
            if DEBUG:
                print(self.tables[name].info())

        if DEBUG:
            print(self.df.info())

        self._set_options()

    def _slice(self, df: pd.DataFrame) -> pd.DataFrame:
        """ Select a time window inside the database. """

        # Find the indices closest to the window boundaries
        first = df.index.searchsorted(self.start)
        last = df.index.searchsorted(self.stop)
        return df.ix[first:last]

    def _make_background(self):
        """ Draw the postal code boundaries on a new figure. """

        fig = plt.figure(figsize=FIGSIZE)
        ax = fig.add_subplot(111)
        ax.set_xlabel('lon')
        ax.set_ylabel('lat')
        ax.set_aspect(1.5)

        shp = self._read_plz()
        plz = shp['geometry']
        plz.plot(alpha=.1, axes=ax)

        return ax

    @staticmethod
    def _print_header(title):
        """ A wide horizontal section title. """
        print('{begin}{title:{fill}{align}100}{end}'
              .format(title=title, fill=FILL, align=CENTER, begin=LEAP, end=LEAP))

    @staticmethod
    def _set_options():
        """ Set plotting options. """
        pd.set_option('display.mpl_style', STYLE)
        plt.rc('font', family=FONT, size=FONTSIZE)

    @staticmethod
    def _unique(path: str, file: str) -> str:
        """ Return a unique filepath. """
        (base, extension) = splitext(file)
        stamp = sub(r'[:]|[-]|[_]|[.]|[\s]', '', str(datetime.now()))
        unique = base.ljust(20, FILL) + stamp + extension
        path = join(path, unique)
        print('Saved %s' % path)
        return path

    @staticmethod
    def _prepare_image(title):
        """ Return a new figure handle. """
        fig = plt.figure(figsize=FIGSIZE, tight_layout=True)
        fig.suptitle(title)
        return fig

    def _make_image(self, file):
        """ Save and show the figure. """
        plt.savefig(self._unique(OUTPUT, file))
        plt.show(block=True)

    @staticmethod
    def _read_plz() -> GeoDataFrame:
        """ Read in Berlin postal code data from the shapely file. """

        # To read in a GeoDataFrame from a file, geopandas will actually assume that
        # the following 3 files live in the same folder: SHP.shp, SHP.dbf and SHP.shx.
        plz = GeoDataFrame.from_file(SHP)
        plz.set_index('PLZ99', inplace=True)
        plz.sort()

        if DEBUG:
            # Print the GeoDataFrame
            pd.set_option('expand_frame_repr', False)
            print(plz, end=LEAP)
            print(plz.describe(), end=LEAP)
            print(plz.info(), end=LEAP)

        return plz

    @staticmethod
    def repair_prices(prices):
        """ Correct the price information. """
        # There are lots of zeros in the prices because the database model was
        # forcing zero as the default for missing values. This is now fixed.
        return prices.replace(0, np.nan, inplace=True)

    def monthly_income(self):
        """ A timeseries plot of the monthly income. """

        income = self.df[['city_tour',
                          'overnight',
                          'waiting_time',
                          'extra_stops',
                          'fax_confirm']]

        monthly = income.resample('M', how='sum')

        ax = monthly.plot(kind='bar',
                          stacked=True,
                          figsize=FIGSIZE,
                          title='Monthly income',
                          fontsize=FONTSIZE)

        ax.xaxis.set_minor_formatter(DateFormatter('%y'))
        ax.set_xlabel('Months')
        ax.set_ylabel('Income (€)')
        plt.tight_layout()

        self._make_image('monthly_income.png')

    def price_histogram(self):
        """ A histogram of job prices stacked by type. """

        prices = self.tables['orders'][['city_tour',
                                        'overnight',
                                        'waiting_time',
                                        'extra_stops',
                                        'fax_confirm']]

        # FIXME Remove hard set x-axis limit
        ax = prices.plot(kind='hist',
                         stacked=True,
                         bins=40,
                         xlim=(1, 30),
                         figsize=FIGSIZE,
                         title='Job price distribution',
                         fontsize=FONTSIZE)

        ax.set_ylabel('Number of jobs')
        ax.set_xlabel('Job price (€)')
        plt.tight_layout()
        self._make_image('price_histogram.png')

    def price_vs_km(self):
        """ A scatter plot of the wage per kilometer. """

        scatter = self.df[['city_tour', 'distance']]

        ax = scatter.plot(kind='scatter',
                          x='distance',
                          y='city_tour',
                          figsize=FIGSIZE,
                          title='Wage vs distance',
                          fontsize=FONTSIZE)

        ax.set_ylabel('Job distance (km)')
        ax.set_ylabel('Job price (€)')
        plt.tight_layout()

        self._make_image('price_vs_km.png')

    def cumulative_km(self):
        """ A cummulative timeseries of job distances. """

        km = self.df[['distance']]
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

        self._make_image('cummulative_km.png')


class MonthVisualizor(Visualizer):

    def __init__(self, df: pd.DataFrame, start, stop):
        super(MonthVisualizor, self).__init__(df, start, stop)

    def streetcloud(self):
        """ A wordcloud of street names using Andreas Müller's code. """

        assert isfile(MASK), 'Could not find {file} for the mask.'.format(file=MASK)

        word_series = self.df[WORDS].dropna()
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
        self._make_image('wordcloud.png')

    def plz_chloropeth(self):
        """ A chloropeth map of Berlin postal codes using pick-up & drop-off frequencies. """

        # Grab Berlin postal codes.
        postal_codes = self.df['postal_code'].dropna()
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
            self._print_header('Chloropeth debug info...')
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

        self._make_image('plz_checkin_map.png')

    def daily_income(self):
        """ A timeseries plot of the daily income. """

        db = self.df.reset_index()
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

        self. _make_image('daily_income.png')


class DayVisualizor(Visualizer):

    def __init__(self, df: pd.DataFrame, start, stop):
        super(DayVisualizor, self).__init__(df, start, stop)

    def pickups_n_dropoffs(self):
        """ Spatial map of checkpoints (split pick-ups and drop-offs). """

        pickups = self.df[(self.df['city'] == 'Berlin') & (self.df['purpose'] == 'pickup')]
        dropoffs = self.df[(self.df['city'] == 'Berlin') & (self.df['purpose'] == 'dropoff')]

        if DEBUG:
            self._print_header('Pickups...')
            print(pickups)
            self._print_header('Dropoffs...')
            print(dropoffs)

        ax = self._make_background()
        ax.plot(pickups['lon'], pickups['lat'], 'k.', markersize=12)
        ax.plot(dropoffs['lon'], dropoffs['lat'], 'b.', markersize=12, alpha=0.5)

        plt.title('Pick-ups (black) and drop-offs (blue)')
        self._make_image('lat_lon.png')


def visualize(time_window: tuple, option: str):
    """ Visualize data by day, month or year. """

    assert time_window[0] <= time_window[1], 'Cannot return to the future'
    print('Starting data visualization...')

    u = User(username='m-134',
             password='PASSWORD',
             db_file='m-134-v2.sqlite')

    v = Visualizer(u.df, u.tables, *time_window)

    if option == '-year':
        v.monthly_income()
        v.price_histogram()
        v.cumulative_km()
        v.price_vs_km()

    elif option == '-month':
        m = MonthVisualizor(u.df, u.tables, *time_window)
        m.daily_income()
        m.plz_chloropeth()
        m.streetcloud()

    elif option == '-day':
        d = DayVisualizor(u.df, u.tables, *time_window)
        d.pickups_n_dropoffs()

if __name__ == '__main__':
    option_ = '-year'
    time_window_ = datetime(2013, 1, 1), datetime(2013, 12, 31, hour=23, minute=59)
    visualize(time_window_, option_)