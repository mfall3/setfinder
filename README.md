## setfinder
# INCOMPLETE
### So far, just gets author affiliation information for crossref authors with keyword in affiliation, and extracts the crossref dois.
*set of scripts to help find datasets related to articles by authors with a given affiliation*

These tools are not perfect, in part because metadata is inconsistently associated with dois, but this approach produced human-usable spreadsheets toward answering the question: "Where are datasets associated with scholary works with authors associated with my institution?" for us at the University of Illinois at Urbana-Champaign.

There are a series of scripts because things can go wrong along the way, and it may be necessary to somewhat manually recover and retry for one step before starting the next one. For example, if there is a timeout or some other error getting one batch of crossref dois, you can get the most recent cursor and use that to try again without restarting from the beginning. Also, this would make it easier to use the script for one of the steps on information gathered some other way.

### 1.) Customize an initial configuration.
Copy config.yml.example to config.yml in working directory. Customizable values can be edited in config.yml. Most of the defaults are reasonable, and by default the paths are filenames for the current directory, but the default affiliation keyword spam is probably not what you want. For example, Urbana was an effective keyword for the University of Illinois at Urbana-Champaign.

### 2.) Fetch crossref dois with affiliated authors.

fetch\_crossref\_works\_by\_affiliation.py

The crossref metadata schema includes affiliation for authors, and their API exposes affilation as query field. For results sets beyond 10K, crossref exposes a cursor to deep page through the results. If cursors are used, they will be logged in the logfile, named setfinder.log in the current directory by default. If the script is interrupted, the most recent cursor can be configured in the initial\_cursor value of in the config.yaml file. The default value of asterisk(\*) is used to start from the beginning. The potential need to restart with a new cursor is the reason only one keyword can be configured a time.

This script uses the crossref API to search for works by authors with affiliations that contain the keyword from the affiliation\_keyword key in the config.yaml file. The output is a file contianing lines of pipe-delimted records in the form crossref\_doi|author\_name|author\_affiliation. The default name for this file is crossref\_affiliations.csv, but this can be changed with the value of the crossref\_affiliations\_path key in the config.yaml file. There is no header row, to better support restarts.

### 3.) Extract set of distinct dois from file created in step 2.

extract\_crossref\_dois.py

This script generates a list of unique crossref dois from an ordered pipe-delimited list that starts with crossref dois. As input, it uses the filepath value from the crossref\_affiliations\_path key in the config.yaml file. As output, it uses the filepath value from the crossref\_dois\_path key in the config.yaml file. The format of the output file is one doi per line.