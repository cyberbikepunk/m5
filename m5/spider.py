""" The spider crawls the company website and downloads webpages showing user data. """


from os.path import join
from os.path import isfile
from datetime import date
from bs4 import BeautifulSoup
from re import findall
from collections import namedtuple
from logging import debug
from glob import glob

from m5.settings import JOB_QUERY_URL, SUMMARY_URL, JOB_FILENAME


Stamped = namedtuple('Stamped', ['stamp', 'data'])
Stamp = namedtuple('Stamp', ['user', 'date', 'uuid'])
RawData = namedtuple('Data', ['info', 'addresses'])


def download_one_day(day, user):
    """
    Download the user webpages for that day, save them to file and return
    a list of beautiful soup objects. Do not download things twice: serve
    webpages from cache where possible.
    """

    assert isinstance(day, date), 'Argument must be a date object'
    assert day <= date.today(), 'Cannot return to the future.'

    s = Spider(day, user)

    if s.has_no_jobs:
        return None

    uuids = s.get_job_uuids()

    if not uuids:
        soups = None
        debug('Skipped %s', day)

    else:
        soups = list()

        for s.uuid in uuids:
            if s.job_is_cached:
                soup = s.load_job()
                debug('Loaded %s', s.job_url)
            else:
                soup = s.download_job()
                s.save_job(soup)
                debug('Downloaded %s', s.job_url)

            soups.append(Stamped(s.stamp, soup))

    return soups


class Spider(object):
    def __init__(self, day, user):
        self._downloads = user.downloads
        self._session = user.session
        self._user = user.username
        self._date = day
        self.uuid = None

    def get_job_uuids(self):
        uuids = self._fish_job_uuids()

        if uuids is None and self._session:
            self._scrape_job_uuids()

        return uuids

    def _fish_job_uuids(self):
        pattern = self._date_string + '-uuid-*.html'
        filepaths = glob(join(self._downloads, pattern))

        if filepaths:
            return [filepath[-12:-5] for filepath in filepaths]

    def _scrape_job_uuids(self):
        payload = {'status': 'delivered', 'datum': self._date.strftime('%d.%m.%Y')}
        response = self._session.get(SUMMARY_URL, params=payload)

        pattern = 'uuid=(\d{7})'
        jobs = findall(pattern, response.text)

        if jobs:
            return set(jobs)

    def download_job(self):
        return BeautifulSoup(self._session.get(self.job_url).text)

    @property
    def stamp(self):
        return Stamp(self._user, self._date, self.uuid)

    @property
    def _date_string(self):
        return self._date.strftime('%d-%m-%Y')

    @property
    def job_url(self):
        return JOB_QUERY_URL.format(uuid=self.uuid, date=self._date.strftime('%d.%m.%Y'))

    @property
    def _job_filepath(self):
        return join(self._downloads, JOB_FILENAME.format(date=self._date_string, uuid=self.uuid))

    @property
    def _no_jobs_filepath(self):
        return join(self._downloads, JOB_FILENAME.format(date=self._date_string, uuid='NO_JOBS'))

    @property
    def job_is_cached(self):
        if isfile(self._job_filepath):
            return True

    def save_job(self, soup):
        with open(self._job_filepath, 'w+') as f:
            f.write(soup.prettify())

    def load_job(self):
        with open(self._job_filepath, 'r') as f:
            html = f.read()
        return BeautifulSoup(html)

    def has_no_jobs(self):
        # If we have already tried to download data for that day
        # and found there was nothing, there will be an empty file
        # yyyy-mm-dd-uuid-NO_JOBS.html in the downloads folder.
        if isfile(self._no_jobs_filepath):
            return True
