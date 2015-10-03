""" This modules orchestrates the data migration from the company server to the local database. """


from logging import info
from datetime import timedelta

from m5.user import initialize
from m5.scraper import scrape
from m5.pipeline import _call_geocoder, process, archive
from m5.spider import fetch_one_day


def migrate(**options):
    """ Migrate user data from the company website to the local database. """

    info('Starting migration process')

    start_date = options.pop('begin')
    stop_date = options.pop('end')
    period = stop_date - start_date

    user = initialize(**options)

    for day in range(period.days):
        date = start_date + timedelta(days=day)
        webpages = fetch_one_day(date, user.web)

        for webpage in webpages:
            job = scrape(webpage)
            tables = process(job)
            archive(user.db_session, tables)

    info('Finished the migration process')
    user.quit()
