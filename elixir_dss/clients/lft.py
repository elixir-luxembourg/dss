from dataclasses import dataclass
from datetime import datetime as dt, timedelta as td

from flask import Flask

try:
    from lftclient import LFTClient, LFTClientException
except ImportError:
    LFTClient = None
    LFTClientException = Exception


@dataclass
class LFTLink:
    id: str
    absolute_url: str
    expiration_date: dt
    password: str


class LFTHandler:
    def __init__(self, app: Flask | None = None):
        self.client: LFTClient | None = None
        self.namespace_id: str | None = None
        if app:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        if LFTClient is None:
            self.client = None
            app.logger.warning("lftclient not installed")
            return

        lft_host = app.config.get("LFT_HOST")
        lft_port = app.config.get("LFT_PORT")
        lft_scheme = app.config.get("LFT_SCHEME")
        lft_username = app.config.get("LFT_USERNAME")
        lft_password = app.config.get("LFT_PASSWORD")
        lft_namespace_id = app.config.get("LFT_NAMESPACE_ID")
        links_url = app.config.get("LFT_LINKS_BASE_URL")

        if all(
            [
                lft_host,
                lft_port,
                lft_scheme,
                lft_username,
                lft_password,
                lft_namespace_id,
                links_url,
            ]
        ):
            self.client = LFTClient(
                host=lft_host, port=lft_port, scheme=lft_scheme, verify_ssl=True
            )
            self.namespace_id = lft_namespace_id
            self.username = lft_username
            self.password = lft_password
            self.links_url = links_url
            self.link_validity_days = app.config.get("LFT_LINK_VALIDITY_DAYS", 1)
            app.logger.info("LFT client initialized")
        else:
            app.logger.warning("LFT not configured")

    def get_or_create_link(self, dataset: "Dataset", sub: str) -> LFTLink:  # noqa: F821
        if not self.client:
            raise RuntimeError("LFT client not initialized")
        try:
            self.client.login(self.username, self.password)
        except LFTClientException as e:
            raise RuntimeError("LFT login failed") from e

        try:
            links = self.client.links_list(
                namespace_id=self.namespace_id, share_name=dataset.id, sub=sub
            )
            if links:
                for link in links:
                    if link.expiration_datetime > dt.now():
                        return LFTLink(
                            id=link.id,
                            absolute_url=self.links_url + link.link_url,
                            expiration_date=link.expiration_datetime,
                            password=link.page_password,
                        )
        except LFTClientException as e:
            raise RuntimeError("LFT link retrieval failed") from e

        try:
            link = self.client.create_link(
                namespace_id=self.namespace_id,
                share_name=dataset.id,
                sub=sub,
                expiration_date=dt.date(dt.now() + td(days=self.link_validity_days)),
            )
            return LFTLink(
                id=link.id,
                absolute_url=self.links_url + link.link_url,
                expiration_date=link.expiration_datetime,
                password=link.page_password,
            )
        except LFTClientException as e:
            raise RuntimeError("LFT link creation failed") from e


__all__ = ["LFTHandler"]
