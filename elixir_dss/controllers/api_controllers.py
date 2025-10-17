import json
import urllib
from json import dumps
from urllib.error import HTTPError, URLError

from elixir_dss import app


@app.cache.cached(timeout=1800, key_prefix="elu_partners")
def get_elu_partners():
    return get_elu_entities("partners")


@app.cache.cached(timeout=1800, key_prefix="elu_cohorts")
def get_elu_cohorts():
    return get_elu_entities("cohorts")


def get_elu_entities(entity_name):
    entities_json_str = None
    if app.config.get("DAISY_USE") is True:
        try:
            urlEntities = urllib.parse.urljoin(
                app.config.get("DAISY_URL"), "/api/" + entity_name
            )
            with urllib.request.urlopen(urlEntities, timeout=5) as response:
                try:
                    data_from_url = response.read().decode("utf-8")
                    entities_dict = json.loads(data_from_url)
                    if "results" not in entities_dict.keys():
                        raise ValueError("results key not found")
                    entities_json_str = dumps(entities_dict["results"])
                except ValueError as e:
                    app.logger.error(
                        "URL not returning valid Json: %s \nError: %s", urlEntities, e
                    )
        except (HTTPError, URLError) as error:
            app.logger.error(
                "Data not retrieved from URL: %s, \nError: %s", urlEntities, error
            )
        except TimeoutError:
            app.logger.error("Socket timed out from URL: %s", urlEntities)
        finally:
            if not entities_json_str:
                app.logger.info("Defaulting config file")
                entities_json_str = dumps(app.config.get("DATA_INIT")[entity_name])
    else:
        app.logger.info("Defaulting config file")
        entities_json_str = dumps(app.config.get("DATA_INIT")[entity_name])
    return json.loads(entities_json_str)
