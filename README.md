# Elixir Data Submission System (DSS)

## Quick Start (Recommended)

For most users, this is all you need:

```bash
# First time setup (creates venv, installs deps, builds CSS, initializes DB)
./setup_dev.sh

# Start the development server
./run_dev.sh
```

Application runs at **http://127.0.0.1:5000**

**Demo Login Credentials:**
- Admin: `steward1@uni.lu` / `steward1`
- Data Provider: `submitter1@some.edu` / `submitter1`

### Daily Development

**Starting the server:**
```bash
./run_dev.sh
```

**Auto-compile SCSS on file changes (optional, in a separate terminal):**
```bash
cd elixir_dss/static/vendor && npm run watch:css
```

Edit `.scss` files → auto-recompiles → refresh browser to see changes!

## Research Data Submission Process

```mermaid
%%{init: {'theme':'neutral', 'themeVariables': { 'fontFamily':'Arial, sans-serif', 'fontSize':'13px'}}}%%
flowchart LR
    Start([Research<br/>Need]):::start
    
    Start --> Stage1
    
    subgraph Stage1["DRAFT"]
        direction TB
        D1[Admin Creates<br/>Submission]:::admin
        D2[Setup Basic Info]:::task
        D3[Assign Data<br/>Providers]:::admin
        D1 --> D2
        D2 --> D3
    end
    
    Stage1 -->|Admin or<br/>Provider Steers| Stage2
    
    subgraph Stage2["STUDY REGISTRATION"]
        direction TB
        SR1[Data Providers Add:]:::header
        SR2[• Data Declarations<br/>• GDPR Categories<br/>• Study Details<br/>• Ethics Info<br/>• Contacts]:::work
        SR1 --> SR2
    end
    
    Stage2 -->|Admin or<br/>Provider Steers| Stage3
    
    subgraph Stage3["DATA UPLOAD"]
        direction TB
        DU1[Data Providers Add:]:::header
        DU2[• Attachments<br/>• Consent Forms<br/>• Checksums<br/>• Messages<br/>• Upload Info]:::work
        DU1 --> DU2
    end
    
    Stage3 -->|Admin or<br/>Provider Steers| Stage4
    
    subgraph Stage4["COMPLETION"]
        direction TB
        C1[Final Review]:::review
        C2[Export Ready]:::complete
        C1 --> C2
    end
    
    Stage4 --> Export([Export via<br/>CLI]):::final
    
    classDef start fill:#f5f5f5,stroke:#333,stroke-width:2px
    classDef admin fill:#ffcdd2,stroke:#c62828,stroke-width:1.5px
    classDef task fill:#fff,stroke:#666,stroke-width:1px
    classDef header fill:#e3f2fd,stroke:#1565c0,stroke-width:1.5px
    classDef work fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px
    classDef review fill:#fff3e0,stroke:#f57c00,stroke-width:1.5px
    classDef complete fill:#c8e6c9,stroke:#43a047,stroke-width:1.5px
    classDef final fill:#37474f,stroke:#263238,stroke-width:2px,color:#fff
    
    style Stage1 fill:#fafafa,stroke:#666,stroke-width:2px
    style Stage2 fill:#fff8e1,stroke:#f9a825,stroke-width:2px
    style Stage3 fill:#e1f5fe,stroke:#039be5,stroke-width:2px
    style Stage4 fill:#e8f5e9,stroke:#43a047,stroke-width:2px
```

## Manual Setup (Advanced)

Only needed if you want to customize the setup process. Otherwise, use `./setup_dev.sh` above.

### Requirements
- Python 3.12 or newer
- Node.js and npm
- OpenJDK 21+ (for some dependencies)
- **Optional:** [lftpythonclient](https://gitlab.com/uniluxembourg/lcsb/elixir/lft/lftpythonclient) - Required for LFT integration to generate upload links

### Python Environment Setup

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
npm ci                    # Install exact versions from package-lock.json
npm run build:css         # Build SASS to CSS
cd ../../../
```

### Configuration

The setup script automatically creates `.env` file. For manual configuration:

**1. Create settings file:**
```bash
cp .env.template .env
```

**2. Database:** SQLite is configured by default (no setup needed)

**3. Authentication:**
- **CONFIG** (default): Local username/password auth - perfect for development
- **AAI**: ELIXIR OIDC authentication

**4. Secret Key:** For production, generate a secure key:
```python
import os
os.urandom(24)
```
        
### Database Initialization

The `./setup_dev.sh` script handles this automatically. For manual setup:

```bash
./manage.py init-db                                # Initialize DB with default data
./manage.py load-demo-users                        # Create demo users
./manage.py grant-data-steward-access <user_email> # Grant data-steward access to existing user
```

**Create additional admin users:**
```bash
./manage.py create-admin "First" "Last" "email@uni.lu" "elixir_id" "ELU_I_77"
```

### Database Migrations

The application uses Flask-Migrate (Alembic) for database schema changes.

```bash
# Create a new migration after model changes
flask db migrate -m "Description of changes"

# Apply migrations to database
flask db upgrade

# Rollback last migration
flask db downgrade
```


## Running the Application

Use `./run_dev.sh` or manually:

```bash
source ./project_venv/bin/activate
export FLASK_APP=elixir_dss
flask run --debug --port 5000
```

Application available at http://127.0.0.1:5000

**Export submissions:**
```bash
./manage.py export-submissions                    # Export completed
./manage.py export-submissions --all              # Export all
./manage.py export-submissions --submission-id 1  # Export specific
```

## Testing

Dependencies are installed by `./setup_dev.sh`. For manual testing:

```bash
# Run tests
uv run pytest
uv run pytest --cov=elixir_dss --cov-report=term-missing  # With coverage

# Lint and format
uvx ruff check .
uvx ruff format .

# Test across Python versions
uv run tox
```


## Versioning

bumpversion is used to handle versioning.

The semantic versioning format is used: {major}.{minor}.{patch}[-dev]

- **Patch**: Bug fixes only
- **Minor**: New features
- **Major**: Breaking changes

Update version:
```bash
bumpversion {patch,minor,major}
```

## Releasing

Create a release:
```bash
bumpversion release
```

This will:
- Change version from {major}.{minor}.{patch}-dev to {major}.{minor}.{patch}
- Create a commit and tag

Push the commit and tag to git after releasing.

## Deployment

**Update Application on VM:**
```bash
sudo bash /home/elixirdss/app-src/elixir-dss/update_app.sh
```

See `deploy/INSTRUCTIONS.md` for full deployment guide.

## Current Version

**v0.4.0-dev**



