import requests

from elixir_dss import app


class IDServiceError(Exception):
    pass


def generate_id(title: str) -> str:
    if not app.config.get("IDSERVICE_ENDPOINT"):
        raise IDServiceError("ID Service endpoint is not configured")

    try:
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

    except requests.RequestException as e:
        raise IDServiceError(f"ID Service request failed: {e}") from e
