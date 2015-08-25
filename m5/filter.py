from m5.user import User
from m5.user import DataFrame
from m5.datetime import datetime


class Filter():
    pass

    def __init__(self, df, ):
        self.df = df

    @staticmethod
    def slice(df: DataFrame, begin: datetime, end: datetime):
        """ Slice a time window from the pandas dataframe. """
        # Find the indices closest to the window boundaries.
        first = df.index.searchsorted(begin)
        last = df.index.searchsorted(end)
        return df.ix[first:last]


class FilterYear(Filter):
    pass


class FilterMonth(Filter):
    pass


class FilterDay(Filter):
    pass


if __name__ == '__main__':
    u = User()
    f = Filter(u.db)
    print(f.input.joined.info())