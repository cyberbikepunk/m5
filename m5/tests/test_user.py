""" Unit-test for the User module. """


import os
import sys
from pprint import pprint
pprint(sys.path)
from unittest import TestCase
from user import User
print('hi')

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
