# Elixir Data and Computing Platform 

## Quick Start

```bash
# First time setup
./setup_dev.sh

# Run development server
./run_dev.sh
```

Application runs at http://127.0.0.1:5000

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

## Development
## Setting up Development Environment


The project_venv folder is for holding the virtual environment. (Elixir DCP supports Python 3.8+) 

```bash
# Create virtual environment
python3 -m venv project_venv
source ./project_venv/bin/activate
```

Install dependencies with:
 
```bash
pip install -e .[dev]

# Frontend dependencies
cd elixir_dcp/static/vendor
npm ci
cd ../../../
```

## Requirements
 - Python 3.12 or newer
 - JDK (OpenJDK 21 suffices) 
 - nodejs and less (`npm install -g less`)
 
## Configuration

### 1. Create your settings file
```bash
cp elixir_dcp/settings.py.template elixir_dcp/settings.py
```

### 2. Configure authentication method
The platform supports two authentication methods:

* **CONFIG** (local authentication) - Uses username/password pairs defined in `AUTHENTICATION_DICT`
  - Perfect for development and testing
  - Users are authenticated against local database
  
* **AAI** (ELIXIR AAI) - Uses OIDC authentication with ELIXIR AAI
  - Requires valid `client_secrets.json` configuration
  - For production deployments



### 3. Configure database
Update the `SQLALCHEMY_DATABASE_URI` variable in `settings.py`:
 
* **Option 1 - SQLite backend (development)**
    ```python
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'elixir-dcp.db')
    ```
    
* **Option 2 - PostgreSQL backend (production)**
    ```python
    SQLALCHEMY_DATABASE_URI = 'postgresql://[user[:password]@][netloc][:port][/dbname]'
    ```
    
    The project includes a docker compose configuration for PostgreSQL:
    ```python
    SQLALCHEMY_DATABASE_URI = 'postgresql://elixirdcp:elixirdcp@localhost:5432/elixirdcp'
    ```

### 4. Set secret key
For development, any string can be used. For production, generate a secure key:
```python
import os
os.urandom(24)
```
        
## Database Initialization

### Start database (if using Docker PostgreSQL)

1. Copy the environment template and customize if needed:
```bash
cp .env.template .env
```

2. Start the PostgreSQL container:
```bash
docker compose up
```

### Initialize database with default data
```bash
export FLASK_APP=elixir_dcp
./manage.py init-db
```

### Create demo users (for development)
```bash
./manage.py load-demo-users
```

This creates three demo users for CONFIG authentication:
- `steward1@uni.lu` / `steward1` (admin)
- `submitter1@some.edu` / `submitter1` (data_provider)
- `submitter2@some.edu` / `submitter2` (data_provider)

### Create an admin user
```bash
./manage.py create-admin "John" "Doe" "john.doe@acme.edu" "xxxxx@elixir-europe.org" "ELU_I_77"
```



## Running the Application

### Development server
```bash
export FLASK_APP=elixir_dcp
flask run --debug --port 5000

# Or using the manage.py script
./manage.py run
```

The application will be available at http://127.0.0.1:5000

### Export submissions
```bash
# Export completed submissions
./manage.py export-submissions

# Export all submissions
./manage.py export-submissions --all

# Export specific submissions
./manage.py export-submissions --submission-id 1 --submission-id 2
```

## Testing
 
Run tests with pytest:
```bash
pytest

# With coverage
pytest --cov=elixir_dcp
```

Run tests with multiple Python versions using tox:
```bash
tox
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

## Current Version

**v0.4.0-dev**



