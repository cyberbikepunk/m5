""" Global settings for the m5 package. """

from os.path import join, normpath, abspath
from sys import modules


# Flags
DEBUG = True
SHOW = True

# User folders
USER = abspath('.')  # TODO Switch USER to user home dir (use expanduser)
PACKAGE = abspath('.')
OUTPUT = normpath(join(PACKAGE, '../output/'))
DATABASE = normpath(join(PACKAGE, '../db/'))
DOWNLOADS = normpath(join(PACKAGE, '../downloads/'))
TEMP = normpath(join(PACKAGE, '../temp/'))
LOG = normpath(join(PACKAGE, '../log/'))

# Files paths
ELUCIDATE = join(LOG, 'elucidate.log')
MASK = join(PACKAGE, 'mask.png')
MASK2 = 'http://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Berlin.svg/1269px-Berlin.svg.png'

# Wordcloud parameters
BLACKLIST = {'strasse', 'allee', 'platz', 'a', 'b', 'c', 'd'}
WORDS = 'street'
MAXWORDS = 200
PROPORTION = 0.8

# URLs to company server
LOGIN = 'http://bamboo-mec.de/ll.php5'
LOGOUT = 'http://bamboo-mec.de/index.php5'
JOB = 'http://bamboo-mec.de/ll_detail.php5'
SUMMARY = 'http://bamboo-mec.de/ll.php5'

# Readability
FILL = '.'
CENTER = '^'
SKIP = '\n\n'
FONTSIZE = 14


def show_settings():
    """ Echo all package parameters. """

    print('Settings for M5 package:', end=SKIP)
    objects = dir(modules[__name__])
    # Only setting parameters are uppercase
    items = [x for x in objects if x.isupper()]

    for item in items:
        value = getattr(modules[__name__], item)
        print('{item} = {value!r}'
              .format(item=item.rjust(20, ' '), value=value))


if __name__ == '__main__':
    show_settings()

