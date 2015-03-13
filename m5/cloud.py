""" Create the wordcloud using Andreas Müller's code cloned from : https://github.com/amueller/word_cloud. """

from m5.settings import DEBUG, MASK, WORDS, BLACKLIST, MAXWORDS, PROPORTION, POP, FIGSIZE
from m5.utilities import make_graph
from m5.user import User

from wordcloud import WordCloud
from string import punctuation, whitespace
from scipy import misc
from numpy.core import ndarray
from numpy import vectorize
from os.path import isfile
from pandas import DataFrame
from matplotlib.pyplot import imshow, axis


def make_cloud(db: DataFrame):
    """ Create the wordcloud using Andreas Müller's code. """

    if not isfile(MASK):
        message = 'Could not find {file} for the mask.'.format(file=MASK)
        raise FileNotFoundError(message)

    image = prepare_mask(MASK)
    text = assemble_text(db['all'])
    cloud = compute_cloud(text, image)
    save_image(cloud)


def get_mask():
    """ Any image can be used as a mask. """
    pass


def prepare_mask(mask) -> ndarray:
    """ Create an cloud mask with mask.png (in the m5 package directory). """

    original = misc.imread(mask)
    flattened = original.sum(axis=2)

    if DEBUG:
        print(flattened.dtype)
        print(flattened.shape)
        print(flattened.max())
        print(flattened.min())

    # The problem is that the resulting mask is
    # the exact reverse of what we want. So...
    def invert(x):
        return 0 if x > 0 else 1

    invert_all = vectorize(invert)
    inverted = invert_all(flattened)

    return inverted


def assemble_text(db: DataFrame)-> str:
    """ Assemble the text for the algorithm. """

    word_series = db[WORDS].dropna()
    word_list = word_series.values
    word_string = whitespace.join(word_list).replace(punctuation, whitespace)

    return word_string


def compute_cloud(words: str, mask: ndarray):
    """ Deliver the wordcloud image. """

    wordcloud = WordCloud(stopwords=BLACKLIST,
                          max_words=MAXWORDS,
                          prefer_horizontal=PROPORTION,
                          mask=mask)

    return wordcloud.generate(words)


def save_image(wordcloud):
    """ Pop the image to the screen. """

    if POP:
        imshow(wordcloud)
        axis("off")

    make_graph('wordcloud.png')


if __name__ == '__main__':
    user = User()
    make_cloud(user.db)
