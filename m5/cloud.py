""" Create the wordcloud using Andreas Müller's code cloned from : https://github.com/amueller/word_cloud. """

from settings import DEBUG, MASK, WORDS, BLACKLIST, MAXWORDS, PROPORTION, POP, FIGSIZE
from utilities import make_image
from user import User

from wordcloud import WordCloud
from string import punctuation, whitespace
from scipy import misc
from numpy.core import ndarray
from numpy import vectorize
from os.path import isfile
from pandas import DataFrame, Series
from matplotlib.pyplot import imshow, axis


def make_cloud(db: DataFrame):
    """ Create the wordcloud using Andreas Müller's code. """

    if not isfile(MASK):
        message = 'Could not find {file} for the mask.'.format(file=MASK)
        raise FileNotFoundError(message)

    words = assemble_text(db['all'][WORDS])
    wordcloud = WordCloud(stopwords=BLACKLIST,
                          max_words=MAXWORDS,
                          prefer_horizontal=PROPORTION,
                          mask=prepare_mask(MASK))

    cloud = wordcloud.generate(words)
    save_image(cloud)
    return cloud


def prepare_mask(mask) -> ndarray:
    """ Create a background mask with mask.png in ~/.m5/assets/. """

    original = misc.imread(mask)
    flattened = original.sum(axis=2)

    if DEBUG:
        print(flattened.dtype)
        print(flattened.shape)
        print(flattened.max())
        print(flattened.min())

    # With the image that I use, the problem is that the
    # resulting mask is the exact reverse of what I want. So...
    def invert(x):
        return 0 if x > 0 else 1

    invert_all = vectorize(invert)
    inverted = invert_all(flattened)
    return inverted


def assemble_text(text: Series)-> str:
    """ Assemble the text for the algorithm. """
    word_series = text.dropna()
    word_list = word_series.values
    word_string = whitespace.join(word_list).replace(punctuation, whitespace)
    return word_string


def save_image(wordcloud: WordCloud):
    """ Pop the image to the screen and save it. """
    if POP:
        imshow(wordcloud)
        axis("off")
    make_image('wordcloud.png')


if __name__ == '__main__':
    user = User()
    make_cloud(user.db)
