""" The PyPi packaging magic happens here. """

import re
import os
import codecs


def read(*parts):
    """ Return the contents of the file. Assume UTF-8 encoding. """
    here = os.path.abspath(path.dirname(__file__))
    with codecs.open(os.path.join(here, *parts), "rb", "utf-8") as f:
        return f.read()


def find_version(*file_paths):
    """ Return the 'VERSION' parameter value from inside the text file. """
    version_file = read(*file_paths)
    version_match = re.search(r"^VERSION = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


# So the following is heavily commented cause I'm going up the learning curve.
# https://hynek.me/articles/sharing-your-labor-of-love-pypi-quick-and-dirty/
from setuptools import setup, find_packages

setup(name='m5',
      license='GPL3',
      author='cyberbikepunk',
      author_email='loic@cyberpunk.bike',
      description='M5 analyses my bike messenger data.',

      # This seems to be the common trick.
      long_description=read('README.md'),

      # The version counter inside VERSION.txt gets incremented
      # automatically each time I run bumpversion in the terminal.
      version=find_version('VERSION.txt'),

      # Point the package url to the online documentation.
      url='http://m5.readthedocs.org/en/latest/',

      # This project is not just a single file module:
      # it's a package with multiple subpackages.
      # We could explictely list all the python
      # packages, but instead we let setuptools do
      # all the the work for us. The top-level tests
      # package will be included but won't be installed.
      # Actually, I don't understand why it shouldn't.
      packages=find_packages(exclude=['tests*']),

      # Miscellaneous files like data files that don't officially
      # belong to a python package, i.e. a directory of python
      # files including __init__.py, need to be included 'by hand'
      # in the MANIFEST file. Here we tell setuptools to use it!
      include_package_data=True,

      # The following parameter 'duplicates' the requirements.txt file.
      # This feature (it's a feature) is discussed at length online.
      # Read the blog post by Donald Stufft to get a better idea
      # (https://caremad.io/2013/07/setup-vs-requirement/). Ideally I
      # think it's better to do the reverse of what I do here, i.e.
      # pass a complete list of depencies to install_requires and
      # and write the requirements file like so:
      #
      # --index-url https://pypi.python.org/simple/
      # -e .
      #
      # The first line is the pip repository. The second tells
      # requirements to read the list in the setup.py script.
      install_requires=read('requirements.txt').splitlines(),

      # PyPI will refuse packages with unknown classifiers.
      # So to avoid uploading a private package by mistake,
      # the trick is to use an unregognized classifier, say
      # 'Private :: Do Not Upload'. Classifiers are listed at
      # https://pypi.python.org/pypi?:action=list_classifiers.
      # Here I'm uploading a public package.
      classifiers=['Development Status :: 3 - Alpha',
                   'Intended Audience :: End Users/Desktop',
                   'Natural Language :: English',
                   'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
                   'Operating System :: POSIX :: Linux',
                   'Programming Language :: Python :: 3',
                   'Topic :: Artistic Software'])