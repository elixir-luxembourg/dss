## Authentication

The system supports two authentication methods, selected via the `AUTHENTICATION_METHOD` environment variable:

### CONFIG Mode

Local authentication with hardcoded credentials in `settings.py`. Intended for development and demo environments only.

### AAI Mode

OIDC-based Single Sign-On via Keycloak (or any OIDC-compliant provider). Set `AUTHENTICATION_METHOD=AAI` and configure `OIDC_AUTHORITY`, `CLIENT_ID`, and `CLIENT_SECRET`.

First-time users are automatically provisioned from the OIDC token claims (`sub`, `email`, `name`) and assigned the `user` role.
