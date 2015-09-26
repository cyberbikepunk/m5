""" A very basic test suite for the user module. """


from unittest import TestCase
from os.path import join
from m5.settings import INSTANCE_DIR
from m5.user import User
from m5.main import build_parser


class TestUser(TestCase):
    options = dict()

    def test_returning_user_with_online_mode_off(self):
        self._test_user('offline_off.ini')

    def test_returning_user_with_online_mode_on(self):
        self._test_user('offline_off.ini')

    def test_new_user_with_online_mode_off(self):
        self._test_user('offline_off.ini', new=True)

    def test_new_user_with_online_mode_on(self):
        self._test_user('offline_on.ini', new=True)

    def _get_options(self, test_init_file):
        args_from_file = ['@' + join(INSTANCE_DIR, test_init_file)]
        args = build_parser().parse_args(args_from_file)

        options = vars(args)

        del options['begin']
        del options['end']

        return options

    def _test_user(self, test_init_file, new=False):
        options = self._get_options(test_init_file)
        self.user = User(**options)

        if new:
            self.user.download_dir = '/tmp/downloads'
            self.user.output_dir = '/tmp/output'

        self.user.authenticate()
        self.user.start_db()

        self.assertIsInstance(self.user, User)

    def tearDown(self):
        self.user.quit()
