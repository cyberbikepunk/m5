""" Global settings for the m5 package. """

from os.path import join, abspath, expanduser
from sys import modules
from inspect import stack
from string import whitespace

# Option flags
DEBUG = False
POP = True
OFFLINE = True

# Program folders
USER_DIR = join(expanduser('~'), '.m5', )
PROJECT_DIR = abspath(__file__ + '/../..')
ASSETS_DIR = join(PROJECT_DIR, 'assets')
PACKAGE_DIR = join(PROJECT_DIR, 'm5')
TESTS_DIR = join(PACKAGE_DIR, 'tests')

# Auto-detect if the code is run from a test
IS_TEST = TESTS_DIR in whitespace.join([s[1] for s in stack()])

# User folders
OUTPUT_DIR = join(USER_DIR, 'output')
DATABASE_DIR = join(USER_DIR, 'db')
DOWNLOADS = join(USER_DIR, 'downloads')
TEMP_DIR = join(USER_DIR, 'temp')
LOG_DIR = join(USER_DIR, 'log')

# Assets files
MASK_FILE = join(ASSETS_DIR, 'mask.png')
SHP_FILE = join(ASSETS_DIR, 'berlin_postleitzahlen.shp')
DBF_FILE = join(ASSETS_DIR, 'berlin_postleitzahlen.dbf')

# Log files
SCRAPING_WARNING_LOG = join(LOG_DIR, 'elucidate.log')

# Wordcloud parameters
WORD_BLACKLIST = {'strasse', 'allee', 'platz', 'a', 'b', 'c', 'd'}
WORD_SOURCE = 'street'
MAX_WORDS = 200
HORIZONTAL_WORDS = 0.8

# URLs to the company server
LOGIN_URL = 'http://bamboo-mec.de/ll.php5'
LOGOUT_URL = 'http://bamboo-mec.de/index.php5'
JOB_URL = 'http://bamboo-mec.de/ll_detail.php5'
SUMMARY_URL = 'http://bamboo-mec.de/ll.php5'

# Readability
FILL = '.'
CENTER = '^'
LEAP = '\n\n'
SKIP = '\n'
STEP = ''
BREAK = '\n' + '-'*79

# Matplotlib settings
PLOT_FONTSIZE = 14
FIGURE_SIZE = (18, 12)
FIGURE_STYLE = 'default'
FIGURE_FONT = 'Droid Sans'
BACKGROUND_ALPHA = 0.


def show_settings():
    """ Echo all. """

    print('Settings for M5 package:', end=LEAP)
    objects = dir(modules[__name__])
    # As far as I know, only setting parameters are uppercase.
    parameters = [x for x in objects if x.isupper()]

    for p in parameters:
        value = getattr(modules[__name__], p)
        print('{item} = {value!r}'
              .format(item=p.rjust(20, ' '), value=value))


if __name__ == '__main__':
    show_settings()

