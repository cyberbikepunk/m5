""" This modules orchestrates the data migration from the company server to the local database. """


from logging import info
from datetime import timedelta

from m5.user import initialize
from m5.scraper import scrape_job
from m5.pipeline import geocode, package, archive
from m5.spider import download_one_day


def migrate(**options):
    """ Migrate user data from the company website to the local database. """

    info('Starting migration process')

    start_date = options.pop('begin')
    stop_date = options.pop('end')
    period = stop_date - start_date

    user = initialize(**options)

    for day in range(period.days):
        date = start_date + timedelta(days=day)
        webpages = download_one_day(date, user.web_session)

        for webpage in webpages:
            job = scrape_job(webpage)

            geolocations = []
            for address in job.addresses:
                geolocations.append(geocode(address))

            tables = package(job, geolocations)
            archive(tables, user.db_session)

    info('Finished the migration process.')
    user.quit()