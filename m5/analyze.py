"""  The module that produces statistics, maps and plots. """

from m5.settings import FONTSIZE, SHOW
from m5.user import User
from m5.utilities import unique_file

from matplotlib.dates import DateFormatter

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


class Analyzer():
    """ Data analysis tools. """

    def __init__(self, db: pd.DataFrame):
        """ Duplicate the database and set plotting options. """

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

    def monthly_income(self):
        """ A timeseries plot of the monthly income. """

        income = self.db['orders'][['city_tour',
                                    'overnight',
                                    'waiting_time',
                                    'extra_stops',
                                    'fax_confirm',
                                    'date']]

        monthly = income.set_index('date').resample('M', how='sum')

        ax = monthly.plot(kind='bar',
                          stacked=True,
                          figsize=(12, 10),
                          title='Monthly income',
                          fontsize=FONTSIZE)

        ax.xaxis.set_minor_formatter(DateFormatter('%y'))
        ax.set_xlabel('Months')
        ax.set_ylabel('Income (€)')
        plt.tight_layout()

        if SHOW:
            plt.show(block=True)
        else:
            plt.savefig(unique_file('monthly_income.png'))

    def daily_income(self):
        """ A timeseries plot of the daily income. """

        dates = self.db['orders']['date']
        income = self.db['orders'][['city_tour',
                                    'overnight',
                                    'waiting_time',
                                    'extra_stops',
                                    'fax_confirm']]

        prices = pd.concat([income, income.sum(axis=1), dates], axis=1)
        prices.rename(columns={0: 'total'}, inplace=True)

        timeseries = prices.groupby('date').sum()
        total = timeseries['total']
        mean = total.mean()

        fig = plt.figure(figsize=(12, 6))
        ax = fig.add_subplot(111)

        ax.vlines(total.index.values, 0, total.values)
        ax.set_xlabel('Dates')
        ax.set_ylabel('Income (€)')
        ax.set_title('Daily income')
        ax.axhline(mean, color='k')
        plt.tight_layout()

        if SHOW:
            plt.show()
        else:
            plt.savefig(unique_file('daily_income.png'))

    def income_pie(self):
        """ A pie chart of income per job type. """

        income = self.db['orders'][['city_tour',
                                    'overnight',
                                    'waiting_time',
                                    'extra_stops',
                                    'fax_confirm']]

        breakdown = income.sum(axis=0)
        breakdown.plot(kind='pie',
                       figsize=(12, 10),
                       title='Income breakdown',
                       fontsize=FONTSIZE)

        if SHOW:
            plt.show()
        else:
            plt.savefig(unique_file('income_pie.png'))

    def cummulative_km(self):
        """ A cummulative timeseries of job distances. """

        km = self.db['orders'][['date', 'distance']]

        accumulated = km.set_index('date').resample('D', how='sum').replace(np.nan, 0).cumsum()
        print(accumulated)

        x = accumulated.index.values
        y = accumulated.values

        with plt.style.context('fivethirtyeight'):
            fig = plt.figure(figsize=(12, 6))
            ax = fig.add_subplot()

            ax.plot(x, y, 'r')
            ax.set_xlabel('time')
            ax.set_ylabel('km')
            ax.set_title('cummulative kms')

        if SHOW:
            plt.show(block=True)
        else:
            plt.savefig(unique_file('cummulative_km.png'))

    def plz_histogram(self):
        """ A histogramm of of postal code frequencies. """

        plz = self.db['all']['postal_code']
        print(self.db['all'])
        ax = plz.plot(kind='hist',
                      bins=40,
                      xlim=(0, 30),
                      figsize=(12, 10),
                      title='Postal code frequencies',
                      fontsize=FONTSIZE)

        ax.set_ylabel('Number of checkins')
        ax.set_xlabel('Postal codes')
        plt.tight_layout()

        if SHOW:
            plt.show(block=True)
        else:
            plt.savefig(unique_file('plz_histogram.png'))

    def price_histogram(self):
        """ A histogramm of job prices stacked by type. """

        prices = self.db['orders'][['city_tour',
                                    'overnight',
                                    'waiting_time',
                                    'extra_stops',
                                    'fax_confirm']]

        ax = prices.plot(kind='hist',
                         stacked=True,
                         bins=40,
                         xlim=(0, 30),
                         figsize=(12, 10),
                         title='Job price distribution',
                         fontsize=FONTSIZE)

        ax.set_ylabel('Number of jobs')
        ax.set_xlabel('Job price (€)')
        plt.tight_layout()

        if SHOW:
            plt.show()
        else:
            plt.savefig(unique_file('price_histogram.png'))

    def price_vs_km(self):
        """ A scatter plot of the wage per kilometer. """

        scatter = self.db['orders'][['city_tour', 'distance']]

        ax = scatter.plot(kind='scatter',
                          x='distance',
                          y='city_tour',
                          figsize=(12, 10),
                          title='Wage vs distance',
                          fontsize=FONTSIZE)

        ax.set_ylabel('Job distance (km)')
        ax.set_ylabel('Job price (€)')
        plt.tight_layout()

        if SHOW:
            plt.show()
        else:
            plt.savefig(unique_file('price_vs_km.png'))

if __name__ == '__main__':

    user = User()
    a = Analyzer(user.db)

    # a.daily_income()
    # a.income_pie()
    # a.price_histogram()
    # a.price_vs_km()
    # a.monthly_income()
    # a.cummulative_km()

    a.plz_histogram()