import requests

from elixir_dss import app


@app.cache.cached(timeout=1800, key_prefix="elu_partners")
def get_elu_partners():
    return get_elu_entities("partners")


@app.cache.cached(timeout=1800, key_prefix="elu_projects")
def get_elu_projects():
    return get_elu_entities("projects")


def _get_default_elu_entities(entity_name):
    app.logger.info("Defaulting config file")
    return app.config.get("DATA_INIT", {}).get(entity_name, [])


def get_elu_entities(entity_name):
    if not app.config.get("DAISY_USE"):
        return _get_default_elu_entities(entity_name)

    try:
        daisy_url = app.config.get("DAISY_URL")
        api_key = app.config.get("DAISY_API_KEY")
        result = requests.get(
            f"{daisy_url}/api/{entity_name}",
            params={
                "API_KEY": api_key,
                "fields": "external_id,acronym,name",
                "published": "true",
            },
            timeout=10,
            verify=app.config.get("DAISY_VERIFY_SSL"),
        )
        result.raise_for_status()
        data = result.json()
        return data.get("items", []) or data.get("results", [])
    except (requests.RequestException, ValueError):
        app.logger.error("Error fetching ELU entities: %s", entity_name)
        return _get_default_elu_entities(entity_name)
