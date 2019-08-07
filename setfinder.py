#!/usr/bin/env python
"""This script generates a list of datasets in figshare
   related to articles with creators affiliated with the
   University of Illinois at Urbana-Champaign
   by Colleen Fallaw at University of Illinois Urbana-Champaign 2019
"""

import logging
import os.path
import requests

def setup(output_filename):
    """Set up the csv file for output result.
        arguments:
            output_filename -- the filename to use for output
        return: None
    """
    if not os.path.exists(output_filename):
        with open(output_filename, "w") as outfile:
            outfile.write("crossref_doi,figshare_doi\n")
        outfile.close()

def process_batches(output_filename):
    """Process all batches of crossref_dois.
        arguments:
            output_filename -- the filename to use for output
        return: None
    """
    crossref_list, next_cursor = (crossref_batch("*"))
    if crossref_list is None:
        LOGGER.warning("crossref_list is None after the first call to crossref_batch")
        return None
    if next_cursor is None:
        LOGGER.warning("next_cursor is None after the first call to crossref_batch")
        return None
    if not crossref_list:
        return None
    process_batch(crossref_list, output_filename)
    while (crossref_list is not None) and (next_cursor is not None):
        LOGGER.info("next_cursor: %s", next_cursor)
        crossref_list, next_cursor = (crossref_batch(next_cursor))
        if not crossref_list:
            LOGGER.warning("crossref_list is None in loop")
            return None
        process_batch(crossref_list, output_filename)
    return None

def process_batch(crossref_list, output_filename):
    """Process a batch of crossref_dois.
        arguments:
            crossref_list -- a list of dois from crossref to process
            output_filename -- the filename to use for output
        return: None
    """
    for crossref_doi in crossref_list:
        related_dois = related_identifiers(crossref_doi)
        if related_dois is not None:
            for related_identifier in related_dois:
                if doi_in_figshare(related_identifier):
                    with open(output_filename, "a") as outfile:
                        outfile.write(crossref_doi + "," + related_identifier + "\n")
                    outfile.close()

def crossref_batch(cursor):
    """Fetch a batch of crossref records for works with creators from Illinois.

        arguments:
            cursor -- the cursor to use in the query to fetch batch
        return: List of dois
    """

    dois = []
    endpoint = "http://api.crossref.org/works"
    params = "query.affiliation=Urbana&select=DOI&cursor=" + cursor

    data = fetch_data(endpoint, params)
    if not data:
        LOGGER.warning("not data for cursor: %s", cursor)
        return([], None)
    items = data.get("message").get("items")
    if not items:
        LOGGER.warning("not items for curosr: %s", cursor)
        return([], None)
    for item in items:
        dois.append(item.get("DOI"))
    new_next_cursor = data.get("message").get("next-cursor")
    return (dois, new_next_cursor)

def related_identifiers(doi):
    """Fetch a list of related doi from scholex for passed in doi.

        arguments:
          doi -- the doi for which to fetch the related dois
        return: List of related identifiers or None
    """
    endpoint = "https://api.scholexplorer.openaire.eu/v2/Links/"
    params = "sourcePid=" + doi
    related_ids = []
    data = fetch_data(endpoint, params)

    if not data:
        return None
    results = data.get("result")
    if not results:
        return None
    for result in results:
        identifiers = result.get("source").get("Identifier")
    if not identifiers:
        return None
    for identifier in identifiers:
        if identifier.get("IDScheme") == "doi":
            related_ids.append(identifier.get("ID"))
    if related_ids:
        return related_ids
    return None

def doi_in_figshare(doi):
    """Determine if a given doi is in figshare.

        arguments:
          doi -- the doi for which to make the determination
        return: True if doi is found in figshare, False if it is not
    """

    endpoint = "https://api.figshare.com/v2/articles"
    params = "doi=" + doi
    data = fetch_data(endpoint, params)
    if not data:
        return False
    return len(data) > 0

def fetch_data(endpoint, params, attempt_number=1):
    """Fetch data from provided url

        arguments:
          url -- the url from which to fetch the data
          attempt_number
        return: data fetched from url
    """

    max_attempts = 10
    try:
        data = None
        response = requests.get(endpoint, params, headers={"Accept": "application/json"})
        LOGGER.info(response.text)
        if not response:
            LOGGER.warning("not response")
            return None
        data = response.json()
        if not data:
            return None
        return data
    except requests.exceptions.RequestException as request_exception:
        LOGGER.warning("Failed, trying again for url: %s", endpoint + "?" + params)
        next_attempt = attempt_number + 1
        if next_attempt > max_attempts:
            LOGGER.warning("Failed max attempts for url: %s", endpoint + "?" + params)
            LOGGER.warning(request_exception)
            return None
        return fetch_data(endpoint, params, next_attempt)

# main
if __name__ == '__main__':
    # setup logging
    logging.basicConfig(
        filename='setfinder.log',
        level=logging.INFO,
        format='%(asctime)s %(levelname)s - %(funcName)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M',
    )
    LOGGER = logging.getLogger(__name__)
    OUTPUT_FILENAME = "out.txt"
    setup(OUTPUT_FILENAME)
    process_batches(OUTPUT_FILENAME)
