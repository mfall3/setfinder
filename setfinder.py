#!/usr/bin/env python
"""This script generates a list of datasets in figshare
associated with crossref works from Illinois."""

# utility to find datasets in figshare related to articles with creators
# affiliated with the University of Illinois at Urbana-Champaign
# by Colleen Fallaw at University of Illinois Urbana-Champaign 2019

import sys
import os.path
import urllib.request
import json

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
        sys.exit("crossref_list is None after the first call to crossref_batch")
    if next_cursor is None:
        sys.exit("next_cursor is None after the first call to crossref_batch")
    print("next_cursor: %s", next_cursor)
    if not crossref_list:
        sys.exit()
    process_batch(crossref_list, output_filename)
    while (crossref_list is not None) and (next_cursor is not None):
        print(format("next_cursor: %s", next_cursor))
        crossref_list, next_cursor = (crossref_batch(next_cursor))
        if not crossref_list:
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
    try:
        dois = []
        url_base = "http://api.crossref.org/works?"
        url_q = "query.affiliation=University%20of%20Illinois,%20Champaign&select=DOI&cursor="
        with urllib.request.urlopen(url_base + url_q + urllib.parse.quote(cursor)) as url:
            data = json.loads(url.read().decode())
        if data is None:
            msg = "data was None in crossref_batch"
            sys.exit(msg)
        items = data.get("message").get("items")
        if items is None:
            msg = "items was None in crossref_batch"
            sys.exit(msg)
        if not items:
            print("no items in crossref batch")
            return None
        for item in items:
            dois.append(item.get("DOI"))
        new_next_cursor = data.get("message").get("next-cursor")
        return (dois, new_next_cursor)
    except urllib.error.URLError as url_error:
        print(url_error)
        return ([], None)

def related_identifiers(doi):
    """Fetch a list of related doi from scholex for passed in doi.

        arguments:
          doi -- the doi for which to fetch the related dois
        return: List of related identifiers or None
    """
    try:
        endpoint = "https://api.scholexplorer.openaire.eu/v2/Links/?sourcePid="
        related_ids = []
        with urllib.request.urlopen(endpoint + doi) as url:
            data = json.loads(url.read().decode())
            if data is None:
                msg = "data was None in related_dois for " + doi
                sys.exit(msg)
            results = data.get("result")
            if results is None:
                return None
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
    except urllib.error.URLError as url_error:
        print(url_error)
        return None

def doi_in_figshare(doi):
    """Determine if a given doi is in figshare.

        arguments:
          doi -- the doi for which to make the determination
        return: True if doi is found in figshare, False if it is not
    """
    try:
        endpoint = "https://api.figshare.com/v2/articles?doi="
        with urllib.request.urlopen(endpoint + doi) as url:
            data = json.loads(url.read().decode())
            if data is None:
                return False
            return len(data) > 0
    except urllib.error.URLError as url_error:
        print(url_error)
        return False

# main
if __name__ == '__main__':
    OUTPUT_FILENAME = "out.txt"
    setup(OUTPUT_FILENAME)
    process_batches(OUTPUT_FILENAME)
