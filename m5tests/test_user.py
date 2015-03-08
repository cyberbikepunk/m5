""" Unit-test for the User module. """

import os

from unittest import TestCase
from m5.user import User


class TestUser(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testUser(self):
        user = User('m-134', 'PASSWORD')
        try:
            user.quit()
        except SystemExit:
            os._exit(0)
