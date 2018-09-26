# Elixir Data and Computing Platform 
## Development



The project_venv folder is for holding the virtual environment. (Elixir DCP has been developed using Python 3.6) 

```bash
virtualenv --python=/usr/local/bin/python3.6  project_venv
source ./project_venv/bin/activate
```

Install dependencies with:
 
```bash
pip install -e .[dev]
```
 
## Configuration

- create a copy of elixir_dcp/settings.py.template as elixir_dcp/settings.py  
- edit the file settings.py to change the path to the sqlite database `SQLALCHEMY_DATABASE_URI`
and the secret `SECRET_KEY`.
For development, any string can be used as a secret key.
For production, generate a good secret key with:

```python
import os
os.urandom(24)
```

## Running

```bash
./manage.py runserver
```

## Testing
 
Run tests with:
 
```bash
python setup.py test
```

Tox can also be used to run the tests with different python versions:

```bash
tox
```


## Versioning

bumpversion is used to handle versioning.

The semantic versioning format is used: {major}.{minor}.{patch}[-dev]

Patch should be used only for bug fixes releases  
Minor should be used for small new features  
Major should be used for major changes  

Use 
```bash
bumpversion {patch, minor, major}
```

to update the version number.

## Releasing

Executing
```bash
bumpversion release
```

will:

- change the version number from {major}.{minor}.{patch}-dev to {major}.{minor}.{patch}
- create a commit and a tag

Once done, the commit and the tag needs to be pushed to git.

## Current Version

**v0.2.0**



