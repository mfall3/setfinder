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
import os.path
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
    initial_cursor = APP_CONFIG["initial_cursor"]
    expected_result_count = result_count(keyword)
    if not expected_result_count:
        LOGGER.warning("no results expected for keyword")
        return None
    LOGGER.warning("expected number of results: %s", str(expected_result_count))
    if expected_result_count > 10000:
        process_cursor_batches(output_filename, keyword)
    else:
        process_offset_batches(output_filename, keyword)
        
def process_cursor_batches(output_filename, keyword):
    crossref_list, next_cursor = (crossref_batch(APP_CONFIG["initial_cursor"], keyword))
    if not crossref_list is None:
        LOGGER.warning("no crossref_list is the first call to crossref_batch")
        return None
    if next_cursor is None:
        LOGGER.warning("next_cursor is None after the first call to crossref_batch")
        return None
    process_batch(crossref_list, output_filename)
    while (crossref_list is not None) and (next_cursor is not None):
        # to avoid rate limiting interfereing with results
        time.sleep(5)
        LOGGER.info("next_cursor: %s", next_cursor)
        crossref_list, next_cursor = (crossref_batch(next_cursor))
        if not crossref_list:
            LOGGER.warning("crossref_list is None in loop")
            return None
        process_batch(crossref_list, output_filename)
    return None

def process_offset_batches(output_filename, keyword, expected_result_count):
    #TODO
    pass

def process_batch(crossref_list, output_filename):
    """Process a batch of crossref_dois.
        arguments:
            crossref_list -- a list of tuples (doi, author_name, author_affiliatin)
                             from crossref to write to outfile
            output_filename -- the filename to use for output
        return: None
    """
    for crossref_tuple in crossref_list:
        with open(output_filename, "a") as outfile:
            outfile.write(crossref_tuple[0] + "|" + crossref_tuple[1] + "|" + crossref_tuple[2] + "\n")
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
            family_name = author.get("family")
            if not family_name:
                LOGGER.warning("no family name for author in item")
                continue
            given_name = author.get("given")
            if not given_name:
                LOGGER.warning("no given name for author in item")
                continue
            name = given_name + " " + family_name
            affiliations = author.get("affiliation")
            if not affiliations:
                continue
            tuples.append((doi, name, affiliations[0].get("name")))
    return tuples      

def crossref_offset_batch(offset, keyword):
    """Fetch a batch of crossref records for works with creators from Illinois.
       Use a cursor because total results is higher than 10K

        arguments:
            cursor -- the cursor to use in the query to fetch batch
            result -- the json result from crossref query
        return: List of tuples(crossref_doi, author_name, author_affiliation)
    """
    endpoint = "http://api.crossref.org/works"
    query = "?rows=1000&query.affiliation=" + keyword + "&select=DOI,author&offset=" + str(offset)
    url_string = endpoint + query
    result = fetch_data(url_string)
    tuples = crossref_result_to_list(result)
    return tuples
    
def crossref_cursor_batch(cursor, keyword):
    """Fetch a batch of crossref records for works with creators from Illinois.
       Use a cursor because total results is higher than 10K

        arguments:
            cursor -- the cursor to use in the query to fetch batch
            result -- the json result from crossref query
        return: List of tuples(crossref_doi, author_name, author_affiliation)
    """

    encoded_cursor = cursor.replace("+", "%2B")
    endpoint = "http://api.crossref.org/works"
    query = "?rows=1000&query.affiliation=" + keyword + "&select=DOI,author&cursor=" + encoded_cursor
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
    #TODO validate inputs
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
        filename = APP_CONFIG["log_path"],
        level = logging.INFO,
        format = '%(asctime)s %(levelname)s - %(funcName)s: %(message)s',
        datefmt = '%Y-%m-%d %H:%M',
    )
    LOGGER = logging.getLogger(__name__)
    main()
