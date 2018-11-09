# coding=utf-8
import json
import urllib
from json import dumps
from urllib.error import HTTPError, URLError
from socket import timeout
from elixir_dcp import app



@app.cache.cached(timeout=1800, key_prefix='elu_partners')
def get_elu_partners():
    partners_json_str = None
    try:
        urlPartners = urllib.parse.urljoin(app.config.get('DAISY_URL'), '/api/partners')
        with urllib.request.urlopen(urlPartners, timeout=5) as response:
            try:
                data_from_url = response.read().decode('utf-8')
                json.loads(data_from_url)
                partners_json_str = data_from_url
            except ValueError as e:
                app.logger.error('URL not returning valid Json: %s \nError: %s', urlPartners, e)
    except (HTTPError, URLError) as error:
        app.logger.error('Partner Data not retrieved from URL: %s, \nError: %s', urlPartners, error)
    except timeout:
        app.logger.error('Socket timed out from URL: %s', urlPartners)
    finally:
        if not partners_json_str:
            app.logger.info('Defaulting config file')
            partners_json_str = dumps(app.config.get('DATA_INIT')['collab_institutions'])
    return json.loads(partners_json_str)

@app.cache.cached(timeout=1800, key_prefix='elu_cohorts')
def get_elu_cohorts():
    cohorts_json_str = None
    try:
        urlCohorts = urllib.parse.urljoin(app.config.get('DAISY_URL'), '/api/cohorts')
        with urllib.request.urlopen(urlCohorts, timeout=5) as response:
            try:
                data_from_url = response.read().decode('utf-8')
                json.loads(data_from_url)
                cohorts_json_str = data_from_url
            except ValueError as e:
                app.logger.error('URL not returning valid Json: %s \nError: %s', urlCohorts, e)
    except (HTTPError, URLError) as error:
        app.logger.error('Partner Data not retrieved from URL: %s, \nError: %s', urlCohorts, error)
    except timeout:
        app.logger.error('Socket timed out from URL: %s', urlCohorts)
    finally:
        if not cohorts_json_str:
            app.logger.info('Defaulting config file')
            cohorts_json_str = dumps(app.config.get('DATA_INIT')['cohorts'])
    return json.loads(cohorts_json_str)



