""" This modules orchestrates the data migration from the company server to the local database. """



def scrape_one_day(soups):

    assert soups is not None, 'Cannot scrape nothing.'
    jobs = list()

    for i, soup in enumerate(soups):
        job, addresses = scrape_job(soup)
        fields = Stamped(soup.stamp, (job, addresses))
        jobs.append(fields)

        debug('(%s/%s) Scraped: %s', len(soups), i+1, _job_url_query)

    return jobs


