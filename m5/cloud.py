""" Choose a column in the database and generate a wordcloud. """

from m5.utilities import DEBUG

from sqlalchemy.engine import Engine
from wordcloud import WordCloud
from string import punctuation, whitespace
from scipy import misc
from numpy.core import ndarray
from numpy import vectorize
from os.path import isfile

import pandas as pd
import matplotlib.pyplot as plt


class StreetCloud():

    BASE = 'street'
    MASK = '/home/loic/downloads/berlin.png'

    BLACKLIST = {'strasse',
                 'allee',
                 'platz',
                 'a', 'b', 'c', 'd'}

    def __init__(self, engine: Engine):
        """ Pull database tables into Pandas. """

        self.clients = pd.read_sql_table('client', engine, index_col='client_id')
        self.orders = pd.read_sql('order', engine, index_col='order_id')
        self.checkins = pd.read_sql('checkin', engine, index_col='checkin_id')
        self.checkpoints = pd.read_sql('checkpoint', engine, index_col='checkpoint_id')

        if DEBUG:
            pd.set_option('display.width', 300)
            pd.set_option('max_columns', 20)

            print(self.clients)
            print(self.orders)
            print(self.checkins)
            print(self.checkpoints)

    def prepare_mask(self) -> ndarray:
        """ Create a mask from an image. """

        if not isfile(self.MASK):
            message = 'Could not find {file} for the mask.'.format(file=self.MASK)
            raise FileNotFoundError(message)

        original = misc.imread(self.MASK)
        flattened = original.sum(axis=2)

        if DEBUG:
            print(flattened.dtype)
            print(flattened.shape)
            print(flattened.max())
            print(flattened.min())

            plt.imshow(flattened)
            plt.show()

        # The problem is that the resulting image is
        # the exact reverse of what we want. So...
        def invert(x):
            return 0 if x > 0 else 1

        invert_all = vectorize(invert)
        inverted = invert_all(flattened)

        return inverted

    def assemble_text(self)-> str:
        """ Assemble the text for the wordcloud algorithm. """

        a = pd.merge(self.checkins,
                     self.checkpoints,
                     left_on='checkpoint_id',
                     right_index=True,
                     how='outer')

        word_list = a[self.BASE].dropna().values
        words = whitespace.join(word_list).replace(punctuation, whitespace)

        return words

    def create_cloud(self, words: str, berlin: ndarray):
        """
        Create the wordcloud using Andreas Müller's code, which
        is cloned from : https://github.com/amueller/word_cloud.
        """

        if DEBUG:
            print(berlin.dtype)
            print(berlin.shape)
            print(berlin.max())
            print(berlin.min())

        wordcloud = WordCloud(stopwords=self.BLACKLIST,
                              max_words=200,
                              prefer_horizontal=0.8,
                              mask=berlin)

        wordcloud.generate(words)

        plt.imshow(wordcloud)
        plt.axis("off")
        plt.show()
