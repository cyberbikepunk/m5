""" The spider crawls the company website and downloads webpages containing user data. """


from os.path import join
from datetime import date
from bs4 import BeautifulSoup
from re import findall
from collections import namedtuple
from logging import debug
from glob import glob

from m5.settings import JOB_URL_FORMAT, SUMMARY_URL, JOB_FILE_FORMAT, UUID

Stamped = namedtuple('Stamped', ('stamp', 'data'))
Stamp = namedtuple('Stamp', ('user', 'date', 'uuid'))
RawData = namedtuple('Data', ('info', 'addresses'))


def download(day, user):
    """
    Download the user webpages for that day, save them to file and return
    a generator of beautiful soup objects. Do not download things twice:
    serve webpages from cache where possible.
    """

    assert isinstance(day, date), 'Argument must be a date object'
    assert day <= date.today(), 'Cannot return to the future.'

    s = Spider(day, user)

    uuids = s.get_job_uuids_from_cache()

    if not uuids and not user.offline:
        uuids = s.scrape_job_uuids()

    if not uuids:
        debug('No jobs found %s on %s', 'offline' if user.offline else 'online', s.date_string)
        return

    for uuid in uuids:
        stamp = Stamp(user.username, day, uuid)

        if user.offline:
            soup = s.load_job(uuid)
            debug('Loaded from cache %s ', s.job_filepath(uuid))
        else:
            soup = s.download_job(uuid)
            s.save_job(soup, uuid)
            debug('Downloaded %s', s.job_url(uuid))

        yield Stamped(stamp, soup)


class Spider(object):
    def __init__(self, day, user):
        self._archive = user.archive
        self._session = user.web
        self._date = day

    def __repr__(self):
        return '<Spider: %s to %s>' % (self._date, self._archive)

    def get_job_uuids_from_cache(self):
        pattern = self.date_string + '-uuid-**.html'
        filepaths = glob(join(self._archive, pattern))

        if filepaths:
            return [filepath[UUID] for filepath in filepaths]

    def scrape_job_uuids(self):
        pattern = 'uuid=(\d{7})'
        payload = {'status': 'delivered', 'datum': self._date.strftime('%d.%m.%Y')}
        response = self._session.get(SUMMARY_URL, params=payload)
        jobs = findall(pattern, response.text)

        if jobs:
            return set(jobs)

    def download_job(self, uuid):
        response = self._session.get(self.job_url(uuid))
        content = response.content.decode('utf-8').encode()
        return BeautifulSoup(content)

    @property
    def date_string(self):
        return self._date.strftime('%Y-%m-%d')

    def job_url(self, uuid):
        return JOB_URL_FORMAT.format(uuid=uuid, date=self._date.strftime('%d.%m.%Y'))

    def job_filepath(self, uuid):
        return join(self._archive, JOB_FILE_FORMAT.format(date=self.date_string, uuid=uuid))

    def save_job(self, soup, uuid):
        with open(self.job_filepath(uuid), 'w+') as f:
            f.write(soup.prettify())

    def load_job(self, uuid):
        with open(self.job_filepath(uuid), 'r') as f:
            html = f.read()
        return BeautifulSoup(html)
