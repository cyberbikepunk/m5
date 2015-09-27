""" A very basic test suite for the user module. """


from unittest import TestCase, skipIf
from os.path import join, isdir
from shutil import rmtree, copyfile
from sqlalchemy.engine import Engine
from m5.settings import DUMMY_DIR, ASSETS_DIR, DB_FILENAME
from m5.user import User, UserError
from os import getenv


credentials = {'username': getenv('BAMBOO_USERNAME'), 'password': getenv('BAMBOO_PASSWORD')}
WARNING = 'Please export BAMBOO_USERNAME and BAMBOO_PASSWORD in your environment'
no_credentials = not all(credentials.values())


@skipIf(no_credentials, WARNING)
class TestUserOnline(TestCase):

    def setUp(self):
        self._initialize_dummy_user(**credentials)

    def tearDown(self):
        rmtree(DUMMY_DIR)
        self.user.quit()

    def test_user_is_created(self):
        self.assertIsInstance(self.user, User)

    def test_user_has_db_engine(self):
        self.assertIsInstance(self.user.engine, Engine)

    def test_user_has_folders(self):
        self.assertTrue(all(list(map(isdir, self.user.folders))))

    def _initialize_dummy_user(self, create=True, **options):
        self.user = User(**options)
        self._set_dummy_folders()

        if create:
            self._create_dummy_install()

        self.user.authenticate()
        self.user.start_db()

    def _set_dummy_folders(self):
        self.user.output_dir = join(DUMMY_DIR, 'output')
        self.user.output_dir = join(DUMMY_DIR, 'downloads')
        self.user.user_dir = DUMMY_DIR

    def _create_dummy_install(self):
        self.user.install()

        assets_db_filepath = join(ASSETS_DIR, DB_FILENAME)
        dummy_db_filepath = join(self.user.user_dir, DB_FILENAME)
        copyfile(assets_db_filepath, dummy_db_filepath)


@skipIf(no_credentials, WARNING)
class TestUserOffline(TestUserOnline):
    def setUp(self):
        self._initialize_dummy_user(offline=True, **credentials)


@skipIf(no_credentials, WARNING)
class TestNewUserOnline(TestUserOnline):
    def setUp(self):
        self._initialize_dummy_user(create=False, **credentials)


class TestWrongCredentials(TestCase):
    def setUp(self):
        self.user = User(username='wrong', password='credentials')

    def test_user_is_created(self):
        self.assertRaises(UserError)


class TestNewUserOffline(TestWrongCredentials):
    def setUp(self):
        self.user = User(offline=True, username='new', password='user')
