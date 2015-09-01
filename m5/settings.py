""" Settings for the m5 package. """


from os.path import join, abspath, expanduser
from sys import modules


# Program folders
OUTPUT_DIR = join(expanduser('~'), '.m5', )
PROJECT_DIR = abspath(__file__ + '/../..')
ASSETS_DIR = join(PROJECT_DIR, 'assets')
PACKAGE_DIR = join(PROJECT_DIR, 'm5')
DATABASE_DIR = join(OUTPUT_DIR, 'db')
LOG_DIR = join(OUTPUT_DIR, 'log')
FOLDER_NAMES = {'log', 'charts', 'dowwloads'}

# Assets files
MASK_FILE = join(ASSETS_DIR, 'mask.png')
SHP_FILE = join(ASSETS_DIR, 'berlin_postleitzahlen.shp')
DBF_FILE = join(ASSETS_DIR, 'berlin_postleitzahlen.dbf')
BLUEPRINT_FILE = join(ASSETS_DIR, 'scraping_blueprints.json')
TAGS_FILE = join(ASSETS_DIR, 'webpage_tags.json')
OVERNIGHTS_FILE = join(ASSETS_DIR, 'overnight_types.json')

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

# String constants
JOB_QUERY_URL = 'http://bamboo-mec.de/ll_detail.php5?status=delivered&uuid={uuid}&datum={date}'
FAILURE_REPORT = '{date}-{uuid}: Failed to scrape {field} on line {nb} inside {tag}.'
JOB_FILENAME = '{date}-uuid-{uuid}.html'
FILE_DATE_FORMAT = '%d-%m-%Y'
URL_DATE_FORMAT = '%d.%m.%Y'

# Formatting
FILL = '.'
CENTER = '^'
LEAP = '\n\n'
SKIP = '\n'
STEP = ''
BREAK = '\n' + '-'*79

# Readability
LOGGED_IN = 'erfolgreich'
REDIRECT = 302
EXIT = {'logout': '1'}

# Matplotlib settings
PLOT_FONTSIZE = 14
FIGURE_SIZE = (18, 12)
FIGURE_STYLE = 'default'
FIGURE_FONT = 'Droid Sans'
BACKGROUND_ALPHA = 0.0


def show_settings():
    """ Echo all settings. """

    print('Current m5 settings:', end=LEAP)
    objects = dir(modules[__name__])
    parameters = [x for x in objects if x.isupper()]

    for p in parameters:
        value = getattr(modules[__name__], p)
        print('{item} = {value!r}'.format(item=p.rjust(20, ' '), value=value))


if __name__ == '__main__':
    show_settings()

