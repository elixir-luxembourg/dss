import requests

from elixir_dss import app


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
