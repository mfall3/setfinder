## setfinder

*set of scripts to help find datasets related to articles by authors with a given affiliation*

These tools are not perfect, in part because metadata is inconsistently associated with dois, but this approach produced human-usable spreadsheets toward answering the question: "Where are datasets associated with scholary works with authors associated with my institution?" for us at the University of Illinois at Urbana-Champaign.

There are a series of scripts because things can go wrong along the way, and it may be necessary to somewhat manually recover and retry for one step before starting the next one. For example, if there is a timeout or some other error getting one batch of crossref dois, you can get the most recent cursor and use that to try again without restarting from the beginning. Also, this would make it easier to use the script for one of the steps on information gathered some other way.

### 0.) Install and configure python 3, install packages

I like conda for this, but installing and configuring python is out of scope for the documentation for this guide.

#### Packages in my environment:
```
  # Name                    Version                   Build  Channel
  asn1crypto                0.24.0                   py37_0
  astroid                   2.2.5                    py37_0
  ca-certificates           2019.5.15                     0
  certifi                   2019.6.16                py37_1
  cffi                      1.12.3           py37hb5b8e2f_0
  chardet                   3.0.4                 py37_1003
  cryptography              2.7              py37ha12b0ac_0
  idna                      2.8                      py37_0
  isort                     4.3.21                   py37_0
  lazy-object-proxy         1.4.1            py37h1de35cc_0
  libcxx                    4.0.1                hcfea43d_1
  libcxxabi                 4.0.1                hcfea43d_1
  libedit                   3.1.20181209         hb402a30_0
  libffi                    3.2.1                h475c297_4
  mccabe                    0.6.1                    py37_1
  ncurses                   6.1                  h0a44026_1
  openssl                   1.1.1c               h1de35cc_1
  pip                       19.1.1                   py37_0
  pycparser                 2.19                     py37_0
  pylint                    2.3.1                    py37_0
  pyopenssl                 19.0.0                   py37_0
  pysocks                   1.7.0                    py37_0
  python                    3.7.3                h359304d_0
  pyyaml                    5.1.1            py37h1de35cc_0
  readline                  7.0                  h1de35cc_5
  requests                  2.22.0                   py37_0
  setuptools                41.0.1                   py37_0
  six                       1.12.0                   py37_0
  sqlite                    3.29.0               ha441bb4_0
  tk                        8.6.8                ha441bb4_0
  urllib3                   1.24.2                   py37_0
  wheel                     0.33.4                   py37_0
  wrapt                     1.11.2           py37h1de35cc_0
  xz                        5.2.4                h1de35cc_4
  yaml                      0.1.7                hc338f04_2
  zlib                      1.2.11               h1de35cc_3
```
### 1.) Customize an initial configuration.
Copy config.yml.example to config.yml in working directory. Customizable values can be edited in config.yml. Most of the defaults are reasonable, and by default the paths are filenames for the current directory, but the default affiliation keyword spam is probably not what you want. For example, Urbana was an effective keyword for the University of Illinois at Urbana-Champaign.

### 2.) Fetch crossref dois with affiliated authors.

fetch\_crossref\_works\_by\_affiliation.py

The crossref metadata schema includes affiliation for authors, and their API exposes affilation as query field. For results sets beyond 10K, crossref exposes a cursor to deep page through the results. If cursors are used, they will be logged in the logfile, named setfinder.log in the current directory by default. If the script is interrupted, the most recent cursor can be configured in the initial\_cursor value of in the config.yaml file. The default value of asterisk(\*) is used to start from the beginning. The potential need to restart with a new cursor is the reason only one keyword can be configured a time.

This script uses the crossref API to search for works by authors with affiliations that contain the keyword from the affiliation\_keyword key in the config.yaml file. The output is a file contianing lines of pipe-delimted records in the form crossref\_doi|author\_name|author\_affiliation. The default name for this file is crossref\_affiliations.csv, but this can be changed with the value of the crossref\_affiliations\_path key in the config.yaml file. There is no header row, to better support restarts.

### 3.) Extract set of distinct dois from file created in step 2.

extract\_crossref\_dois.py

This script generates a list of unique crossref dois from an ordered pipe-delimited list that starts with crossref dois. As input, it uses the filepath value from the crossref\_affiliations\_path key in the config.yaml file. As output, it uses the filepath value from the crossref\_dois\_path key in the config.yaml file. The format of the output file is one doi per line.

### 4.) Fetch related dois from file created in step 3.
fetch\_related\_dois.py

This script generates a list of crossref\_doi|related\_doi lines from a file containing a list of crossref\_dois. As input, it uses the filepath value from the crossref\_dois\_path key in the config.yaml file. As output, it uses the filepath value from the related\_dois\_path key in the config.yaml file.

This data can be imported into excel or other data analytics tool. The related dois can be grouped by doi prefix, and prefixes associated with repositories, to glean insight into distribution.

### 5.) Optional - populate database to perform queries and create reports.
db\_builder.py

This script generates an sqlite database from the pipe-delimited files generated by steps 2 and 4, into a database named from value of the database\_path key in config.yml. By default the database path is setfinder.db in the working directory.

Then you can fire up DB Browser for SQLite or other SQLite tools to explore and report.

