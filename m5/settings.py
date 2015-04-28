""" Global settings for the m5 package. """

from os.path import join, abspath, expanduser
from sys import modules

# Flags
DEBUG = True
POP = True
OFFLINE = True

# Program folders
USER = join(expanduser('~'), '.m5', )
PACKAGE = abspath(__file__ + '/../..')
ASSETS = join(PACKAGE, 'assets')

# User folders
OUTPUT = join(USER, 'output')
DATABASE = join(USER, 'db')
DOWNLOADS = join(USER, 'downloads')
TEMP = join(USER, 'temp')
LOG = join(USER, 'log')

# Assets files
MASK = join(ASSETS, 'mask.png')
SHP = join(ASSETS, 'berlin_postleitzahlen.shp')
DBF = join(ASSETS, 'berlin_postleitzahlen.dbf')

# Log files
ELUCIDATE = join(LOG, 'elucidate.log')

# Wordcloud parameters
BLACKLIST = {'strasse', 'allee', 'platz', 'a', 'b', 'c', 'd'}
WORDS = 'street'
MAXWORDS = 200
PROPORTION = 0.8

# URLs to the company server
LOGIN = 'http://bamboo-mec.de/ll.php5'
LOGOUT = 'http://bamboo-mec.de/index.php5'
JOB = 'http://bamboo-mec.de/ll_detail.php5'
SUMMARY = 'http://bamboo-mec.de/ll.php5'

# Readability
FILL = '.'
CENTER = '^'
LEAP = '\n\n'
SKIP = '\n'
STEP = ''
BREAK = '\n' + '-'*100 + '\n'


# Plotting
FONTSIZE = 14
FIGSIZE = (18, 12)
STYLE = 'default'
FONT = 'Droid Sans'


def show_settings():
    """ Echo all package parameters. """

    print('Settings for M5 package:', end=LEAP)
    objects = dir(modules[__name__])
    # Only setting parameters are uppercase variables.
    parameters = [x for x in objects if x.isupper()]

    for p in parameters:
        value = getattr(modules[__name__], p)
        print('{item} = {value!r}'
              .format(item=p.rjust(20, ' '), value=value))


if __name__ == '__main__':
    show_settings()

