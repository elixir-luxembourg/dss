## Authentication

The system supports two authentication methods (configured in `settings.py`):

### CONFIG Mode 

Local user authentication with hardcoded credentials.

### OIDC Mode 

LCSB SSO (Keycloak) authentication using OIDC.

**Features:**
- Single Sign-On (SSO)
- First-time users complete signup form
- User information pulled from OIDC token
