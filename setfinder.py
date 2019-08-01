# utility to find datasets in figshare related to articles with creators affiliated with the University of Illinois at Urbana-Champaign
# by Colleen Fallaw at University of Illinois Urbana-Champaign 2019

import logging
import sys
import os
import os.path
import urllib.request, json
        
def crossref_batch(next_cursor):
    #:return: Tuple of (dois, next_cursor) or None
    
    dois = []
    
    endpoint = "http://api.crossref.org/works?query.affiliation=University%20of%20Illinois,%20Champaign&select=DOI&cursor="
    with urllib.request.urlopen(endpoint + urllib.parse.quote(next_cursor)) as url:
        data = json.loads(url.read().decode())
        
    if data is None:
        msg = "data was None in crossref_batch"
        logger.warning(msg)
        sys.exit(msg)
          
    items = data.get("message").get("items")
    
    if items is None:
        msg = "items was None in crossref_batch"
        logger.warning(msg)
        sys.exit(msg)
        
    if len(items) == 0:
        print("length of items is 0")
        return None
        
    for item in items:
        dois.append(item.get("DOI"))
        
    new_next_cursor = data.get("message").get("next-cursor")    
    
    return(dois, new_next_cursor)

def related_identifiers(doi):
    
    #:return: List of related identifiers or None
    
  endpoint = "https://api.scholexplorer.openaire.eu/v2/Links/?sourcePid="
  
  related_identifiers = []
  
  with urllib.request.urlopen(endpoint + doi) as url:
      data = json.loads(url.read().decode())
      
      if data is None:
          msg = "data was None in related_identifiers for " + doi
          logger.warning(msg)
          sys.exit(msg)
      results = data.get("result")
      if results is None:
          return None
      if len(results) == 0:
          return None
      for result in results:
          identifiers = result.get("source").get("Identifier")
          if identifiers is None:
              return None
          if len(identifiers) == 0:
              return None
          for identifier in identifiers:
              if identifier.get("IDScheme") == "doi":
                related_identifiers.append(identifier.get("ID"))
  if len(related_identifiers) > 0:
      return related_identifiers
  else:
      return None 
      
def doi_in_figshare(doi):
    
    #:return: True if doi is found in figshare, False if it is not
    
    endpoint = "https://api.figshare.com/v2/articles?doi="
    with urllib.request.urlopen(endpoint + doi) as url:
        data = json.loads(url.read().decode())
      
        if data is None:
            return False
        
        return len(data) > 0 

# main
    
if __name__ == '__main__':
    
    logging.basicConfig(filename='setfinder.log',level=logging.DEBUG, format='%(asctime)s %(message)s')

    logging.info('Starting setfinder.py ...')
    
    output_filename = "out.txt"
        
    if not os.path.exists(output_filename):    
        with open(output_filename,"w") as f:
            f.write("crossref_doi,figshare_doi")
        f.close()
    
    crossref_list, next_cursor = (crossref_batch("*"))
    
    if crossref_list is None:
        sys.exit("crossref_list is None after the first call to crossref_batch")
    
    if next_cursor is None:
        sys.exit("next_cursor is None after the first call to crossref_batch")
        
    logging.info("next_cursor: " + next_cursor)    
        
    if len(crossref_list) == 0:
        sys.exit()        

    for crossref_doi in crossref_list:
        related_dois = related_identifiers(crossref_doi)
        if related_dois is not None:
          for related_identifier in related_dois:
              if doi_in_figshare(related_identifier):
                  with open(output_filename,"a") as f:
                      f.write(crossref_doi + "," + related_identifier)
                  f.close()
                  logging.info("crossref_doi: " + crossref_doi + " figshare_doi: " + related_identifier)

    while (crossref_list is not None) and (next_cursor is not None):
        
        logging.info("next_cursor: " + next_cursor) 
    
        crossref_list, next_cursor = (crossref_batch(next_cursor))
        
        if len(crossref_list) == 0:
            sys.exit()        

        for crossref_doi in crossref_list:
            related_dois = related_identifiers(crossref_doi)
        
            if related_dois is not None:
              for related_identifier in related_dois:
                  if doi_in_figshare(related_identifier):
                      logging.info("crossref_doi: " + crossref_doi + " figshare_doi: " + related_identifier)

    
    
    