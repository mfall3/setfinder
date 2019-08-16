#!/usr/bin/env python
# extract_crossref_dois.py
"""This script generates a list of unique crossref dois
   from an ordered pipe-delimited list that starts with crossref dois
   by Colleen Fallaw at University of Illinois Urbana-Champaign 2019
"""

import sys
import logging
import urllib.request
import urllib.parse
import time
import json
import yaml


def main():
    """Process an ordered pipe-delimited list that starts with crossref dois
       into a list of crossref dois.
    """
    inpath = APP_CONFIG["crossref_affiliations_path"]
    outpath = APP_CONFIG["crossref_dois_path"]
    doi_set = set()
    with open(inpath) as infile:
       line = infile.readline()
       while line:
           row = line.split("|", 3)
           doi = row[0]
           if doi[:3] == "10.":
               doi_set.add(doi)
           line = infile.readline()
    doi_list = list(doi_set)      
    with open(outpath, "w+") as outfile:
        for doi in doi_list:
            outfile.write('%s\n' % doi)
    
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