# Development Guide

## Quick Start

For most contributors, this is all you need:

```bash
# First time setup (creates venv, installs deps, builds CSS, initializes DB)
./setup_dev.sh

# Start the development server
./run_dev.sh
```

Application runs at **http://127.0.0.1:5000**

**Demo Login Credentials:**

| Email | Password | Role |
|-------|----------|------|
| `steward1@uni.lu` | `steward1` | Admin (Data Steward) |
| `submitter1@some.edu` | `submitter1` | Data Provider |
| `submitter2@some.edu` | `submitter2` | Data Provider |

---

## Manual Setup

Only needed if you want to customize the setup process.

### Requirements

- Python 3.12+
- Node.js and npm
- OpenJDK 21+
- **Optional:** [lftpythonclient](https://gitlab.com/uniluxembourg/lcsb/elixir/lft/lftpythonclient) — required for LFT integration to generate upload links

### Python Environment

```bash
# Using UV (recommended)
pip install uv
uv venv project_venv
source ./project_venv/bin/activate
uv pip install -e '.[dev]'
```

### Frontend Dependencies

```bash
cd elixir_dss/static/vendor
npm ci                # Install exact versions from package-lock.json
npm run build:css     # Compile SASS to CSS
cd ../../../
```

**Auto-compile SCSS on file changes (optional, in a separate terminal):**

```bash
cd elixir_dss/static/vendor && npm run watch:css
```

### Configuration

```bash
cp .env.template .env
```

Key settings in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `ELIXIR_DSS_ENV` | Environment (`dev` / `prod`) | `dev` |
| `AUTHENTICATION_METHOD` | `CONFIG` (local) or `AAI` (OIDC) | `CONFIG` |
| `SECRET_KEY` | Flask secret key — change for production | auto-generated |

For production, generate a secure secret key:

```python
import os
os.urandom(24)
```

### Database Initialization

```bash
./manage.py init-db                                # Initialize DB with default data
./manage.py load-demo-users                        # Create demo users
./manage.py grant-data-steward-access <email>      # Grant data steward role to existing user
./manage.py create-admin "First" "Last" "email@uni.lu" "elixir_id" "ELU_I_77"
```

### Running the Application

```bash
source ./project_venv/bin/activate
export FLASK_APP=elixir_dss
flask run --debug --port 5000
```

---

## Database Migrations

The application uses Flask-Migrate (Alembic) for schema changes.

```bash
# Create a migration after model changes
flask db migrate -m "Description of changes"

# Apply pending migrations
flask db upgrade

# Roll back the last migration
flask db downgrade
```

---

## Testing

```bash
# Run tests
uv run pytest

# With coverage
uv run pytest --cov=elixir_dss --cov-report=term-missing --cov-report=xml

# Test across Python versions
uv run tox
```

---

## Linting and Formatting

```bash
uvx ruff check .
uvx ruff format .
```

---

## Code Quality (SonarQube)

```bash
# Generate coverage report first
uv run pytest --cov=elixir_dss --cov-report=xml

# Run SonarQube scanner
sonar-scanner -Dsonar.token=<user-token>
```

---

## Exporting Submissions

```bash
./manage.py export-submissions                    # Export completed submissions
./manage.py export-submissions --all              # Export all submissions
./manage.py export-submissions --submission-id 1  # Export a specific submission
```

---

## Versioning and Releasing

The project uses [semantic versioning](https://semver.org/): `{major}.{minor}.{patch}[-dev]`

| Bump | When |
|------|------|
| `patch` | Bug fixes only |
| `minor` | New features |
| `major` | Breaking changes |

```bash
# Bump version
bumpversion patch   # or minor, or major

# Cut a release (removes -dev suffix, creates commit and tag)
bumpversion release
```

After releasing, push the commit and tag:

```bash
git push && git push --tags
```

Then [create a GitHub release](https://github.com/elixir-luxembourg/dss/releases/new) from the new tag.

---

## Technical Implementation Notes

### Authorization Decorator

The system uses `@app_authorization` for access control:

```python
@app_authorization(
    allowed_roles=['admin', 'data_steward'],
    record_authorization={
        'entity': 'Submission',
        'entity_id_key': 'sub_id',
        'entity_ac_attribute': 'id'
    }
)
```

**Logic:**

1. Check if user is authenticated
2. Check if user has one of the `allowed_roles`
3. If not admin and `record_authorization` is specified:
   - Fetch the entity (e.g. `Submission`)
   - Check if user has a `SubmissionAccess` record for that entity
   - Deny access if none found

### Service Layer

Key functions in `elixir_dss/models/services.py`:

| Function | Description |
|----------|-------------|
| `create_sub()` | Creates a new submission with auto-generated `ref_name` |
| `delete_sub()` | Deletes a submission (only valid in Draft state) |
| `steer_sub()` | Advances submission to the next state and sends notifications |
| `revert_sub()` | Moves submission back to the previous state |
| `has_access()` | Checks whether a user has access to a given submission |
| `get_in_progress_submissions_shared_with_user()` | Returns submissions visible to a data provider |
| `assign_role_to_user()` | Assigns a global role to a user |
| `register_new_user()` | Creates a new user account |
