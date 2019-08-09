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
