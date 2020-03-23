# Elixir Data and Computing Platform 
## Development
## Setting up Development Environment


The project_venv folder is for holding the virtual environment. (Elixir DCP has been developed using Python 3.6) 

```bash
virtualenv --python=/usr/local/bin/python3.6  project_venv
source ./project_venv/bin/activate
```

Install dependencies with:
 
```bash
pip install -e .[dev]

# In case of using zsh as your shell, try the following:
bash -c pip install -e .[dev]
```

## Requirements
 - Python 3.6 or newer
 - JDK (OpenJDK 11 suffices) 
 - nodejs and less (`npm install -g less`) 
 
## Configuration


 * create your ```settings.py``` 
```bash
mv elixir_dcp/settings.py.template elixir_dcp/settings.py
```

 * make database configuration by changing the ```SQLALCHEMY_DATABASE_URI``` variable under ```class Config(object):``` within ```settings.py```:
 
    * Option 1 - SQLLite backend
        
        ```SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'elixir-dcp.db')```
        
    * Option 2 - Postgres backend. 
    
        ```SQLALCHEMY_DATABASE_URI = postgresql://[user[:password]@][netloc][:port][/dbname]```
        
        The project includes a docker-compose.yml to quickly deploy a postgres database for the application, if you use the default dockerised postgres then the connection string would look like
        
        ```SQLALCHEMY_DATABASE_URI = 'postgresql://dish:dish@localhost:4001/dish'```
        
 * set the secret key for the application by manipulating the variable `SECRET_KEY`. For development, any string can be used as a secret key. For production, generate a good secret key with the following commands in a python shell:


        ```python
        import os
        os.urandom(24)
        ```
        
## Initialise the DB

 * (f using dockerised postgres) start the db server:
 
 
         ``` docker-compose up ```

 * run initialisation script:
 
 
         ```./manage.py init_db```
 


## Running the app

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

**v0.3.0-dev**



