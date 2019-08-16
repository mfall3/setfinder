#!/usr/bin/env python
# db_builder.py
"""This script generates an sqlite database
   from pipe-delimited files, such as the ones generated by
   other scripts in the setfinder project.
   by Colleen Fallaw at University of Illinois Urbana-Champaign 2019
"""

import os
import sys
import logging
import sqlite3
import yaml

def create_connection():
    """ create a database connection to the SQLite database
        specified by db_file
    :return: Connection object or None
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        return conn
    except sqlite3.Error as sqlite3_error:
        LOGGER.warning(sqlite3_error)
    return None

def crossref_doi_author():
    """ create and populate table for crossref dois with authors and affiliations
    :return: None
    """
    conn = create_connection()
    if not conn:
        sys.exit("could not connect to database")
    cursor = conn.cursor()

    # Create table
    cursor.execute('''CREATE TABLE crossref_doi_author
                 (crossref_doi text, author_name text, author_affiliation text)''')
    inpath = APP_CONFIG["crossref_affiliations_path"]

    with open(inpath) as infile:
        line = infile.readline()
        while line:
            row = line.split("|", 3)
            doi = row[0]
            if doi[:3] == "10.":
                cursor.execute("INSERT INTO crossref_doi_author VALUES (?,?,?)", row)
                conn.commit()
            line = infile.readline()
    conn.close()

def related_dois():
    """ create and populate table for crossref dois and related dois
    :return: None
    """
    conn = create_connection()
    if not conn:
        sys.exit("could not connect to database")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE related_dois
                 (crossref_doi text, related_doi text)''')

    inpath = APP_CONFIG["related_dois_path"]

    with open(inpath) as infile:
        line = infile.readline()
        while line:
            row = line.split("|", 2)
            crossref_doi = row[0]
            if crossref_doi[:3] == "10.":
                cursor.execute("INSERT INTO related_dois VALUES (?,?)", row)
                conn.commit()
            line = infile.readline()
    conn.close()


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
    DB_FILE = APP_CONFIG["database_path"]
    # start fresh
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    crossref_doi_author()
    related_dois()
