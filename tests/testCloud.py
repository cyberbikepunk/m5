""" A simple unittest script for the streetcloud module. """

from unittest import TestCase
from m5.user import User
from m5.streetcloud import StreetCloud


class TestStreetCloud(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testStreetCloud(self):
        user = User('m-134', 'PASSWORD', local=True)
        cloud = StreetCloud(user.engine)

        mask = cloud.prepare_mask()
        text = cloud.assemble_text()
        cloud.create_cloud(text, mask)