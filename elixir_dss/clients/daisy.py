import requests

from elixir_dss import app


@app.cache.cached(timeout=1800, key_prefix="elu_partners")
def get_elu_partners():
    return get_elu_entities("partners")


@app.cache.cached(timeout=1800, key_prefix="elu_projects")
def get_elu_projects():
    return [p for p in get_elu_entities("projects") if p.get("external_id")]


def _get_default_elu_entities(entity_name):
    app.logger.info("Defaulting config file")
    return app.config.get("DATA_INIT", {}).get(entity_name, [])


def get_elu_entities(entity_name: str, fields: str = "external_id,acronym,name"):
    if not app.config.get("DAISY_USE"):
        return _get_default_elu_entities(entity_name)

    try:
        daisy_url = app.config.get("DAISY_URL")
        api_key = app.config.get("DAISY_API_KEY")
        result = requests.get(
            f"{daisy_url}/api/{entity_name}",
            params={
                "API_KEY": api_key,
                "fields": fields,
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


def get_elu_lcsb_pis(project_id: str = None):
    if not project_id or project_id == "None":
        app.logger.warning("Project ID is None")
        return []

    projects = get_elu_entities("projects", fields="external_id,contacts")

    current_project = None
    for project in projects:
        if project.get("external_id") == project_id:
            current_project = project
            break
    if not current_project:
        app.logger.warning("Project ID %s not found in ELU projects", project_id)
        return []

    contacts = current_project.get("contacts", [])
    result = []
    seen = set()
    for contact in contacts:
        # if contact.get("role") == "Principal_Investigator" # all roles
        entry = {
            "name": f"{contact.get('first_name')} {contact.get('last_name')}",
            "email": contact.get("email"),
        }
        key = (entry["name"], entry["email"])
        if key not in seen:
            seen.add(key)
            result.append(entry)
    return result
