__author__ = 'loic'

import os

from setuptools import setup, find_packages


def read(*paths):
    """Build a file path from *paths* and return the contents."""
    with open(os.path.join(*paths), 'r') as f:
        return f.read()

setup(name='m5',
      version='0.1.0',
      description='Analyse my bike messanger data.',
      long_description=(read('README.rst')),
      url='readthedocs',
      license='GNU3',
      author='cyberbikepunk',
      author_email='loic@cyberpunk.bike',
      py_modules=['m5'],
      include_package_data=True,
      install_requires=open('requirements.txt').read().splitlines(),
      packages=find_packages(exclude=['tests*']),
      classifiers=['Development Status :: 3 - Alpha',
                   'Intended Audience :: End Users/Desktop',
                   'Natural Language :: English',
                   'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
                   'Operating System :: POSIX :: Linux',
                   'Programming Language :: Python :: 3',
                   'Topic :: Artistic Software'])