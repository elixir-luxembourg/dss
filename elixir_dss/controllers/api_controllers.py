import json

import requests

from elixir_dss import app


@app.cache.cached(timeout=1800, key_prefix="elu_partners")
def get_elu_partners():
    return get_elu_entities("partners")


@app.cache.cached(timeout=1800, key_prefix="elu_projects")
def get_elu_projects():
    return get_elu_entities("projects")


def get_elu_entities(entity_name):
    if not app.config.get("DAISY_USE"):
        app.logger.info("Defaulting config file")
        entities_json_str = json.dumps(app.config.get("DATA_INIT")[entity_name])
        return json.loads(entities_json_str)

    try:
        daisy_url = app.config.get("DAISY_URL")
        api_key = app.config.get("DAISY_API_KEY")
        result = requests.get(
            f"{daisy_url}/api/{entity_name}",
            params={"API_KEY": api_key, "fields": "external_id,acronym,name"},
            timeout=10,
            verify=False,
        )
        result.raise_for_status()
        data = result.json()
        return data.get("items", []) or data.get("results", [])
    except (requests.RequestException, ValueError):
        app.logger.error("Error fetching ELU entities: %s", entity_name)
        app.logger.info("Defaulting config file")
        entities_json_str = json.dumps(app.config.get("DATA_INIT")[entity_name])
        return json.loads(entities_json_str)


def generate_id(title: str) -> str:
    if not app.config.get("IDSERVICE_ENDPOINT"):
        app.logger.warning("ID Service endpoint is not set")
        return ""

    response = requests.post(
        f"{app.config.get('IDSERVICE_ENDPOINT')}",
        json={
            "entity": "dataset",
            "name": title,
        },
        timeout=6,
        headers={"Content-Type": "application/json"},
    )
    response.raise_for_status()
    return response.text
