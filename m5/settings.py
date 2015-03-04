""" Global settings for the m5 package. """

from os.path import dirname, join, normpath, isdir, expanduser
from os import mkdir
from sys import modules

# Verbose
DEBUG = True

# Readability
FILL_1 = '-'
FILL_2 = '.'
CENTER = '^'
SKIP = '\n\n'

# Folders
HOME = '.'  # expanduser('~/.m5')
OUTPUT = normpath(join(dirname(__file__), '../output/'))
DATABASE = normpath(join(dirname(__file__), '../db/'))
DOWNLOAD = normpath(join(dirname(__file__), '../downloads/'))
TEMP = normpath(join(dirname(__file__), '../temp/'))
LOG = normpath(join(dirname(__file__), '../log/'))

# HTTP
LOGIN = 'http://bamboo-mec.de/ll.php5'
LOGOUT = 'http://bamboo-mec.de/index.php5'


def create_folders():
    """ Create user folders if needed. """

    folders = (HOME, OUTPUT, DATABASE, DOWNLOAD, TEMP, LOG)

    for folder in folders:
        if not isdir(folder):
            # Don't handle IO exception
            # to get better feedback.
            mkdir(folder, mode=666)
            print('Created {dir}.'.format(dir=folder))


def show_settings():
    """ Echo the package setting parameters. """

    print('m5 package settings:')
    objects = dir(modules[__name__])
    # Assume upper case = setting parameters
    items = [x for x in objects if x.isupper()]

    for item in items:
        value = getattr(modules[__name__], item)
        print('{item} = {value}' .format(item=item, value=value))


if __name__ == '__main__':
    create_folders()
    show_settings()



