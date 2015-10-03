""" A very basic test suite for the user module. """


from unittest import TestCase, skipIf
from os.path import isdir
from sqlalchemy.engine import Engine

from m5.settings import CREDENTIALS_WARNING as WARN, USERNAME, PASSWORD
from m5.user import User, UserError, Ghost


class TestUser(TestCase):
    @skipIf(not USERNAME or not PASSWORD, WARN)
    def test_returning_user_online(self):
        self.user = Ghost().bootstrap().init()
        self._assert_ok()

    def test_returning_user_offline(self):
        self.user = Ghost(offline=True).bootstrap().init()
        self._assert_ok()

    @skipIf(not USERNAME or not PASSWORD, WARN)
    def test_new_user_online(self):
        self.user = Ghost().init()
        self._assert_ok()

    def _assert_ok(self):
        self.assertIsInstance(self.user, User)
        self.assertTrue(all(list(map(isdir, self.user.folders))))
        self.assertIsInstance(self.user.engine, Engine)

    def tearDown(self):
        self.user.clear()
        self.user.logout()

    def test_new_user_offline(self):
        self.user = Ghost(offline=True, username='new', password='user')
        self.assertRaises(UserError, lambda: self.user.init())

