#!/usr/bin/env python
# fetch_related_dois.py
"""This script reads from a file containing a list of crossref dois
   with creators affiliated with the
   University of Illinois at Urbana-Champaign
   fetches related doi information from scholex
   and generates a pipe-delimited list of crossref dois and related dois
   by Colleen Fallaw at University of Illinois Urbana-Champaign 2019
"""
import sys
import logging
import urllib.request
import urllib.parse
import json
import yaml

def related_identifiers(doi):
    """Fetch a list of related doi from scholex for passed in doi.
        arguments:
          doi -- the doi for which to fetch the related dois
        return: List of related identifiers or None
    """
    endpoint = "https://api.scholexplorer.openaire.eu/v2/Links/"
    params = "sourcePid=" + doi
    related_ids = []
    data = fetch_data(endpoint + "?" + params)
    if not data:
        return None
    results = data.get("result")
    if not results:
        return None
    for result in results:
        identifiers = result.get("target").get("Identifier")
        if not identifiers:
            continue
        for identifier in identifiers:
            if identifier.get("IDScheme") == "doi":
                related_ids.append(identifier.get("ID"))
    if related_ids:
        return related_ids
    return None

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
    """ reads crossref dois from infile, writes crossref_doi|related_doi lines to outfile
    """
    input_filename = APP_CONFIG["crossref_dois_path"]
    output_filename = APP_CONFIG["related_dois_path"]
    with open(input_filename) as infile:
        crossref_dois = infile.read().splitlines()
    if not crossref_dois:
        sys.exit("no dois found in file")
    for crossref_doi in crossref_dois:
        related_dois = related_identifiers(crossref_doi)
        if not related_dois:
            continue
        for related_doi in related_dois:
            with open(output_filename, 'a+') as outfile:
                outfile.write(crossref_doi + "|" + related_doi + "\n")

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
    main()
