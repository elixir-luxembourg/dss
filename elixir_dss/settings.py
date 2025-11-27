import os
from dotenv import load_dotenv
from elixir_dss.constants import CONFIG_DATA

# Load environment variables at module import
load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

APP_DATA_BASE_DIR = os.path.abspath(os.path.join(basedir, "../../app-data"))

# Load environment variable
ELIXIR_DSS_ENV = os.environ.get("ELIXIR_DSS_ENV")

# Above command does not work on the deployment server CentOS, so when deploying use below
# APP_DATA_BASE_DIR = '/home/elixirdss/app-data'


class Config(object):
    # name of the application
    TITLE = os.environ.get("APP_TITLE")
    SECRET_KEY = os.environ.get("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(APP_DATA_BASE_DIR, "uploads")
    SUBMISSION_EXPORT_FOLDER = os.path.join(APP_DATA_BASE_DIR, "exports")

    # Menu Bar Items a list of  (Name, Link, Sub item list, role)
    APP_MENU_BAR_ITEMS = [
        (
            "Data Steward",
            None,
            [
                ("Submissions", "list_submissions"),
                ("Email Notifications", "list_notifications"),
            ],
            "data_steward",
        ),
        ("My Submissions", "list_my_submissions", [], "user"),
        ("Admin", None, [("Users", "list_users")], "admin"),
        ("About", "about", [], "public"),
    ]
    DATA_INIT = CONFIG_DATA

    # Configuration from environment variables
    DATA_STEWARDS_MAILS = (
        os.environ.get("DATA_STEWARDS_MAILS").split(",")
        if os.environ.get("DATA_STEWARDS_MAILS")
        else []
    )
    DAISY_USE = os.environ.get("DAISY_USE", "").lower() == "true"
    DAISY_URL = os.environ.get("DAISY_URL")
    DAISY_API_KEY = os.environ.get("DAISY_API_KEY")
    DAISY_VERIFY_SSL = os.environ.get("DAISY_VERIFY_SSL", "true").lower() == "true"

    AUTHENTICATION_METHOD = os.environ.get("AUTHENTICATION_METHOD")
    # a dict containing user and password items for CONFIG based authentication
    AUTHENTICATION_DICT = {
        "steward1@uni.lu": "steward1",
        "submitter1@some.edu": "submitter1",
        "submitter2@some.edu": "submitter2",
        "admin@uni.lu": "admin",
    }

    # OIDC config
    OIDC_SCOPES = (
        os.environ.get("OIDC_SCOPE").split()
        if os.environ.get("OIDC_SCOPE")
        else ["openid", "email", "profile"]
    )
    OIDC_COOKIE_SECURE = os.environ.get("OIDC_COOKIE_SECURE", "").lower() == "true"

    # Flask session configuration
    SESSION_COOKIE_NAME = os.environ.get("SESSION_COOKIE_NAME")
    SESSION_COOKIE_HTTPONLY = (
        os.environ.get("SESSION_COOKIE_HTTPONLY", "").lower() == "true"
    )
    SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE")
    SESSION_COOKIE_SECURE = (
        os.environ.get("SESSION_COOKIE_SECURE", "").lower() == "true"
    )
    PERMANENT_SESSION_LIFETIME = (
        int(os.environ.get("PERMANENT_SESSION_LIFETIME"))
        if os.environ.get("PERMANENT_SESSION_LIFETIME")
        else 3600
    )

    # Keycloak/OIDC settings from environment
    OIDC_AUTHORITY = os.environ.get("OIDC_AUTHORITY")
    CLIENT_ID = os.environ.get("CLIENT_ID")
    CLIENT_SECRET = os.environ.get("CLIENT_SECRET")

    # LFT
    LFT_HOST = os.environ.get("LFT_HOST")
    LFT_PORT = int(os.environ.get("LFT_PORT", "8443"))
    LFT_SCHEME = os.environ.get("LFT_SCHEME", "https")
    LFT_USERNAME = os.environ.get("LFT_USERNAME")
    LFT_PASSWORD = os.environ.get("LFT_PASSWORD")
    LFT_NAMESPACE_ID = int(os.environ.get("LFT_NAMESPACE_ID") or "1")
    LFT_VERIFY_SSL = os.environ.get("LFT_VERIFY_SSL", "true").lower() == "true"
    LFT_LINKS_BASE_URL = os.environ.get("LFT_LINKS_BASE_URL")
    LFT_LINK_VALIDITY_DAYS = int(os.environ.get("LFT_LINK_VALIDITY_DAYS") or "1")

    CACHE_CONFIG = {
        "CACHE_TYPE": "filesystem",
        "CACHE_DIR": "cache",
        "CACHE_THRESHOLD": 10000,
        "CACHE_DEFAULT_TIMEOUT": 300,
    }

    IDSERVICE_ENDPOINT = os.environ.get("IDSERVICE_ENDPOINT")


class ProdConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = True

    # Flask-Mail config
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = (
        int(os.environ.get("MAIL_PORT")) if os.environ.get("MAIL_PORT") else None
    )
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "").lower() == "true"
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")


class DevConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = True

    # Flask-Mail config (inherits from Config, can override via env vars)
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = (
        int(os.environ.get("MAIL_PORT")) if os.environ.get("MAIL_PORT") else None
    )
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "").lower() == "true"
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")


class TestConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "test-elixir-dss.db")

    PRESERVE_CONTEXT_ON_EXCEPTION = False

    ASSETS_DEBUG = True
    TESTING = True
    CACHE_CONFIG = {"CACHE_TYPE": "null"}
    WTF_CSRF_ENABLED = False

    DAISY_USE = True
    DAISY_URL = "https://test-daisy.example.com"
    DAISY_API_KEY = "test_api_key"
