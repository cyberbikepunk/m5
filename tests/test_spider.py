""" Test the spider module. """


from unittest import TestCase, skipIf
from os.path import join, isfile
from datetime import date
from bs4 import BeautifulSoup

from m5.spider import download
from m5.user import Ghost
from m5.settings import USERNAME, PASSWORD, CREDENTIALS_WARNING as WARN


class TestSpider(TestCase):
    def setUp(self):
        self.day = date(2014, 12, 23)

    def tearDown(self):
        self.user.clear()
        self.user.logout()

    def test_load_one_day_from_cache(self):
        self.user = Ghost(offline=True).bootstrap().initialize()
        self._check()

    @skipIf(not USERNAME or not PASSWORD, WARN)
    def test_download_one_day(self):
        self.user = Ghost().bootstrap().flush().initialize()
        self._check()

    def _check(self):
        self.soups = download(self.day, self.user.initialize())

        expected_files = [
            join(self.user.archive, '2014-12-23-uuid-2984702.html'),
            join(self.user.archive, '2014-12-23-uuid-2984750.html'),
            join(self.user.archive, '2014-12-23-uuid-2985351.html'),
        ]

        for soup in self.soups:
            self.assertIsInstance(soup.data, BeautifulSoup)

        for file_path in expected_files:
            self.assertTrue(isfile(file_path))

        with open(expected_files[0]) as f:
            content = f.read()

        self.assertTrue('Straße' in content)
        self.assertTrue('Mühlenstrasse' in content)

        with open(expected_files[2]) as f:
            content = f.read()

        self.assertTrue('Wirtschaftsprüfungsgesellschaft' in content)
