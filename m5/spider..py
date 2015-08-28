""" The spider crawls the company website and downloads webpages showing user data. """


from os.path import join
from os.path import isfile
from datetime import date
from bs4 import BeautifulSoup
from re import findall
from collections import namedtuple
from logging import info

from m5.settings import JOB_QUERY_URL, SUMMARY_URL, JOB_FILENAME


Stamped = namedtuple('Stamped', ['stamp', 'data'])
Stamp = namedtuple('Stamp', ['user', 'date', 'uuid'])


class Spider(object):
    def __init__(self, username=None, session=None, offline=None, downloads=None):
        self._username = username
        self._downloads = downloads
        self._offline = offline
        self._session = session
        self._stamp = None

    def download_one_day(self, day):
        """
        Download the webpages for that day. Save them to file and and return
        a list of beautiful soup objects. Do not download things twice: serve
        webpages from cache if they are available.
        """

        assert isinstance(day, date), 'Argument must be a date object'
        assert day <= date.today(), 'Cannot return to the future.'

        self._stamp = Stamp(self._username, day, 'NO_JOBS')

        if self._has_no_jobs:
            return None

        uuids = self._scrape_job_uuids(day)
        soups = list()

        if not uuids:
            soups = None
            info('No jobs to download on %s', day)
        else:
            for i, uuid in enumerate(uuids):
                self._stamp.uuid = uuid

                if self._job_is_cached:
                    soup = self._load_job()
                    verb = 'Loaded'
                elif not self._offline:
                    soup = self._get_one_job()
                    self._save_job(soup)
                    verb = 'Downloaded'
                else:
                    soup = None
                    verb = 'Skipped'

                info('%s %s/%s: %s', verb, i+1, len(uuids), self._job_url)

                if soup:
                    soups.append(Stamped(self._stamp, soup))

        return soups

    def _scrape_job_uuids(self, day):
        """
        Scrape the uuid query parameter for all jobs
        on a given day by scraping the summary webpage.
        The so called uuids are actually 7 digit numbers.
        """

        pattern = 'uuid=(\d{7})'
        payload = {'status': 'delivered', 'datum': day.strftime('%d.%m.%Y')}
        response = self._session.get(SUMMARY_URL, params=payload)
        jobs = findall(pattern, response.text)

        return set(jobs)

    def _get_one_job(self):
        return BeautifulSoup(self._session.get(self._job_url).text)

    @property
    def _job_filepath(self):
        return join(self._downloads, JOB_FILENAME.format(date=self._stamp.date.strftime('%Y-%m-%d'),
                                                         uuid=self._stamp.uuid))

    @property
    def _job_url(self):
        return JOB_QUERY_URL.format(uuid=self._stamp.uuid,
                                    date=self._stamp.date.strftime('%d.%m.%Y'))

    @property
    def _job_is_cached(self):
        return True if isfile(self._job_filepath) else False

    def _save_job(self, soup):
        with open(self._job_filepath, 'w+') as f:
            f.write(soup.prettify())

    def _load_job(self):
        with open(self._job_filepath, 'r') as f:
            html = f.read()
        return BeautifulSoup(html)

    # If we have already tried to download data for that day
    # and found there was nothing, there will be an empty file
    # yyyy-mm-dd-uuid-NO_JOBS.html in the downloads folder.
    _has_no_jobs = _job_is_cached

