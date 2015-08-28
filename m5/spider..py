from os import path
from os.path import isfile
from datetime import date, timedelta
from requests import Session as RemoteSession
from bs4 import BeautifulSoup
from re import findall


from m5.settings import DEBUG, DOWNLOADS, SCRAPING_WARNING_LOG, JOB_URL, BREAK, SUMMARY_URL, OFFLINE


class Downloader():
    """ The Downloader class fetches html files from the remote server. """

    def __init__(self, remote_session: RemoteSession, overwrite: bool=None):
        assert OFFLINE is False, 'Turn the OFFLINE flag off (in the settings module).'
        self._overwrite = overwrite
        self._remote_session = remote_session
        self._stamp = None

    def bulk_download(self, start_date: date):
        delta = date.today() - start_date
        for d in range(delta.days):
            self.download(start_date + timedelta(days=d))

    def download(self, day: date) -> list:
        """ Download the web-page for each job on that day. Save it and and return a
        list of beautiful soup objects. Serve from cache whenever it's possible.
        """

        assert isinstance(day, date), 'Argument must be a date object'
        assert day <= date.today(), 'Cannot return to the future.'

        # Resets all object properties
        self._stamp = Stamp(day, 'NO_JOBS')

        if self._is_hopeless:
            return None

        uuids = self._scrape_uuids(day)
        soups = list()

        if not uuids:
            soups = None
            if DEBUG:
                print('No jobs to download on {day}.'.format(day=str(day)))
        else:
            for i, uuid in enumerate(uuids):
                self._stamp = Stamp(day, uuid)

                if self._is_cached and not self._overwrite:
                    soup = self._load_job()
                    verb = 'Loaded'
                else:
                    soup = self._get_job()
                    self._save_job(soup)
                    verb = 'Downloaded'

                if DEBUG:
                    print('{verb} {n}/{N}. {url}'.
                          format(verb=verb, n=i+1, N=len(uuids), url=self._job_url))

                soups.append(Stamped(self._stamp, soup))

        return soups

    def _scrape_uuids(self, day: date) -> set:
        """ Return uuid request parameters for each job by scraping the summary page. """

        url = SUMMARY_URL
        payload = {'status': 'delivered', 'datum': day.strftime('%d.%m.%Y')}
        response = self._remote_session.get(url, params=payload)

        # The so called 'uuids' are actually 7 digit numbers.
        pattern = 'uuid=(\d{7})'
        jobs = findall(pattern, response.text)
        return set(jobs)

    def _get_job(self) -> BeautifulSoup:
        """ Fetch the web-page for that day and return a beautiful soup. """

        url = JOB_URL
        payload = {'status': 'delivered',
                   'uuid': self._stamp.uuid,
                   'datum': self._stamp.date.strftime('%d.%m.%Y')}

        response = self._remote_session.get(url, params=payload)
        return BeautifulSoup(response.text)

    @property
    def _is_hopeless(self):
        """ True if we already know that the day contains no jobs. """
        # We've put an empty file stamped 'NO_JOBS' inside the downloads directory.
        return self._is_cached

    @property
    def _filepath(self) -> str:
        """ Where a job's html file is saved. """
        filename = '%s-uuid-%s.html' % (self._stamp.date.strftime('%Y-%m-%d'), self._stamp.uuid)
        return path.join(DOWNLOADS, filename)

    @property
    def _job_url(self) -> bool:
        """ Return the job url for a given day and uuid. """
        return 'http://bamboo-mec.de/ll_detail.php5?status=delivered&uuid={uuid}&datum={date}'\
            .format(uuid=self._stamp.uuid, date=self._stamp.date.strftime('%d.%m.%Y'))

    @property
    def _is_cached(self) -> bool:
        """ True if the html file is found locally. """
        return True if isfile(self._filepath) else False

    def _save_job(self, soup):
        """ Prettify the soup and save it to file. """
        with open(self._filepath, 'w+') as f:
            f.write(soup.prettify())

    def _load_job(self) -> BeautifulSoup:
        """ Load an html file and return a beautiful soup. """
        with open(self._filepath, 'r') as f:
            html = f.read()
        return BeautifulSoup(html)

