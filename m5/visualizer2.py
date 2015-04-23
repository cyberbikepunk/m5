""" A better class-oriented visualization module. """


from settings import DEBUG
from pandas import DataFrame
from datetime import date as Date
from user import User


class Canvas():
    pass

    def pop(self):
        pass

    def save(self):
        pass


class YearCanvas():
            y = YearVisualizor(u.df, *time_window)
        y.monthly_income()
        y.price_histogram()
        y.cumulative_km()
        y.price_vs_km()

class Data():
    def __init__(self, data: DataFrame, tables, start: Date, stop: Date):
        self.start = start
        self.stop = stop
        self.data = self._slice([data])
        self.tables = None

        if DEBUG:
            print(self.data.info())

    def _slice(self, df: DataFrame) -> DataFrame:
        """ Select a time window inside the pandas dataframe. """

        # Find the indices closest to the window boundaries
        first = df.index.searchsorted(self.start)
        last = df.index.searchsorted(self.stop)
        return df.ix[first:last]

    def serve(self, table_name=None):
        if not table_name:
            return self.data
        else:
            return self.tables[table_name]


class Plot():
    def __init__(self, data):
        self._figure = None
        self._axes = None
        self.draw = None
        self.xlabel = None
        self.ylabel = None
        self.title = None
        self.placement = None
        self.file = None

    def define(self):
        pass

    def draw(self):
        pass

    def prepare(self):
        pass


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

    data = Data(u.df, *time_window)

    if option == '-year':
        fig = YearCanvas(data)

    elif option == '-month':
        m = MonthVisualizor(u.df, *time_window)
        m.daily_income()
        m.plz_chloropeth()
        m.streetcloud()

    elif option == '-day':
        d = DayVisualizor(u.df, *time_window)
        d.pickups_n_dropoffs()
