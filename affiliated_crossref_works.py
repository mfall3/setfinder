#!/usr/bin/env python
"""This script generates a list of works in crossref
   with creators affiliated with the
   University of Illinois at Urbana-Champaign
   dois are duplicated to give each author with affilaition a line
   for readability
   by Colleen Fallaw at University of Illinois Urbana-Champaign 2019
"""

import sys
import logging
import urllib.request
import urllib.parse
import time
import json
import yaml

def process_batches(output_filename, keyword):
    """Process all batches of crossref_dois for keyword.
        arguments:
            output_filename -- the filename to use for output
            keyword -- the affiliation keyword use in query
        return: None
    """
    expected_result_count = result_count(keyword)
    if not expected_result_count:
        LOGGER.warning("no results expected for keyword")
        return None
    LOGGER.info("expected number of results: %s", str(expected_result_count))
    if expected_result_count > MAX_OFFSET:
        process_cursor_batches(output_filename, keyword, expected_result_count)
    else:
        process_offset_batches(output_filename, keyword, expected_result_count)
    return None
def process_cursor_batches(output_filename, keyword, expected_count):
    """Process all batches of crossref_dois for keyword, using cursor method.
        arguments:
            output_filename -- the filename to use for output
            keyword -- the affiliation keyword use in query
        return: None
    """
    cumulative_result_count = 0
    num_rows = BATCH_SIZE
    next_cursor = APP_CONFIG["initial_cursor"]
    crossref_list, next_cursor = (crossref_cursor_batch(next_cursor, num_rows, keyword))
    cumulative_result_count = cumulative_result_count + num_rows
    if not crossref_list:
        LOGGER.warning("no crossref_list after the first call to crossref_batch")
        return None
    if next_cursor is None:
        LOGGER.warning("next_cursor is None after the first call to crossref_batch")
        return None
    process_batch(crossref_list, output_filename)
    while (crossref_list is not None) and (next_cursor is not None):
        rows_to_go = expected_count - cumulative_result_count
        if rows_to_go < 1:
            LOGGER.info("Processing complete.")
            break
        if rows_to_go < BATCH_SIZE:
            num_rows = rows_to_go
        # to avoid rate limiting interfereing with results
        time.sleep(5)
        LOGGER.info("next_cursor: %s", next_cursor)
        crossref_list, next_cursor = (crossref_cursor_batch(next_cursor, num_rows, keyword))
        if not crossref_list:
            LOGGER.warning("crossref_list is None in loop")
            break
        process_batch(crossref_list, output_filename)
        cumulative_result_count = cumulative_result_count + num_rows
    return None

def process_offset_batches(output_filename, keyword, expected_count):
    """Process all batches of crossref_dois for keyword, using offset method.
        arguments:
            output_filename -- the filename to use for output
            keyword -- the affiliation keyword use in query
        return: None
    """
    cumulative_result_count = 0
    if expected_count < BATCH_SIZE:
        num_rows = expected_count
    else:
        num_rows = BATCH_SIZE
    result_offset = 0
    crossref_list = (crossref_offset_batch(result_offset, num_rows, keyword))
    if not crossref_list:
        LOGGER.warning("no crossref_list after the first call to crossref_batch")
        return None
    process_batch(crossref_list, output_filename)
    cumulative_result_count = cumulative_result_count + num_rows
    result_offset = cumulative_result_count
    while (crossref_list is not None) and (result_offset is not None):
        if result_offset >= expected_count:
            break
        rows_to_go = expected_count - cumulative_result_count
        if rows_to_go < 1:
            LOGGER.info("Processing complete.")
            break
        if rows_to_go < BATCH_SIZE:
            num_rows = rows_to_go
        # to avoid rate limiting interfereing with results
        time.sleep(5)
        LOGGER.info("result_offset: %s", str(result_offset))
        crossref_list, result_offset = (crossref_offset_batch(result_offset, num_rows, keyword))
        if not crossref_list:
            LOGGER.warning("crossref_list is None in loop")
            return None
        process_batch(crossref_list, output_filename)
        cumulative_result_count = cumulative_result_count + num_rows
        result_offset = cumulative_result_count
    return None

def process_batch(crossref_list, output_filename):
    """Process a batch of crossref_dois.
        arguments:
            crossref_list -- a list of tuples (doi, author_name, author_affiliatin)
                             from crossref to write to outfile
            output_filename -- the filename to use for output
        return: None
    """
    for tup in crossref_list:
        with open(output_filename, "a") as outfile:
            outfile.write(tup[0] + "|" + tup[1] + "|" + tup[2] + "\n")
        outfile.close()
def result_count(keyword):
    """Get the count total expected number of results.
        arguments:
            keyword -- the keyword for the affiliation query
        return: None
    """
    endpoint = "http://api.crossref.org/works"
    query = "?rows=0&query.affiliation=" + keyword
    url_string = endpoint + query
    result = fetch_data(url_string)
    if not result:
        LOGGER.warning("Not result in result_count")
        return None
    return result.get("message").get("total-results")
def crossref_result_to_list(result):
    """Turn the json result of fetching a batch of crossref records into list of tuples.

        arguments:
            result -- json result from crossref query
        return: List of tuples(crossref_doi, author_name, author_affiliation)
    """
    tuples = []
    if not result:
        LOGGER.warning("not result")
        return tuples
    items = result.get("message").get("items")
    if not items:
        LOGGER.warning("not items")
        LOGGER.warning(str(result))
        return tuples
    for item in items:
        doi = item.get("DOI")
        authors = item.get("author")
        if not authors:
            continue
        for author in authors:
            sequence = author.get("sequence")
            if sequence != "first":
                continue
            family_name = author.get("family")
            if not family_name:
                continue
            given_name = author.get("given")
            if not given_name:
                continue
            name = given_name + " " + family_name
            affiliations = author.get("affiliation")
            if not affiliations:
                continue
            for affiliation in affiliations:
                affiliation_name = affiliation.get("name")
                affiliation_name = affiliation_name.replace("\r", " ")
                affiliation_name = affiliation_name.replace("\n", " ")
                tuples.append((doi, name, affiliation_name))
    return tuples

def crossref_offset_batch(offset, num_rows, keyword):
    """Fetch a batch of crossref records for works with creators from Illinois.
       Use a cursor because total results is higher than 10K

        arguments:
            cursor -- the cursor to use in the query to fetch batch
            result -- the json result from crossref query
        return: List of tuples(crossref_doi, author_name, author_affiliation)
    """
    endpoint = "http://api.crossref.org/works"
    query = "?query.affiliation=" + keyword + \
            "&select=DOI,author&rows=" + str(num_rows) + \
            "&offset=" + str(offset)
    url_string = endpoint + query
    result = fetch_data(url_string)
    tuples = crossref_result_to_list(result)
    return tuples

def crossref_cursor_batch(cursor, num_rows, keyword):
    """Fetch a batch of crossref records for works with creators from Illinois.
       Use a cursor because total results is higher than 10K

        arguments:
            cursor -- the cursor to use in the query to fetch batch
            result -- the json result from crossref query
        return: List of tuples(crossref_doi, author_name, author_affiliation)
    """

    encoded_cursor = cursor.replace("+", "%2B")
    endpoint = "http://api.crossref.org/works"
    query = "?query.affiliation=" + keyword + \
            "&select=DOI,author&rows=" + str(num_rows) + \
            "&cursor=" + encoded_cursor
    url_string = endpoint + query
    result = fetch_data(url_string)
    tuples = crossref_result_to_list(result)
    new_next_cursor = result.get("message").get("next-cursor")
    return (tuples, new_next_cursor)

def fetch_data(url_string):
    """Fetch data from provided url

        arguments:
          url -- the url from which to fetch the data
          attempt_number
        return: data fetched from url
    """
    try:
        data = None
        with urllib.request.urlopen(url_string) as url:
            data = json.loads(url.read().decode())
        if not data:
            LOGGER.warning("not data for url: %s", url_string)
            return None
        return data
    except urllib.error.URLError as url_error:
        LOGGER.warning("HTTP get request failed for: %s", url_string)
        LOGGER.warning(url_error)
        return None

def main():
    """Sets global constants and initiates processing of
       batches of crossref results
    """
    output_filename = APP_CONFIG["crossref_affiliations_path"]
    keyword = APP_CONFIG["affiliation_keyword"]
    process_batches(output_filename, keyword)

# main
if __name__ == '__main__':
    # load config
    with open("config.yml", 'r') as stream:
        try:
            APP_CONFIG = yaml.safe_load(stream)
        except yaml.YAMLError as yaml_error:
            print(yaml_error)
            sys.exit("could not load config.yaml file")
    # setup logging
    logging.basicConfig(
        filename=APP_CONFIG["log_path"],
        level=logging.INFO,
        format='%(asctime)s %(levelname)s - %(funcName)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M',
    )
    LOGGER = logging.getLogger(__name__)
    BATCH_SIZE = APP_CONFIG["batch_size"]
    MAX_OFFSET = 10000
    main()
