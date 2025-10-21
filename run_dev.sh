#!/bin/bash
source ./project_venv/bin/activate
export FLASK_APP=elixir_dss
flask run --debug --port 8000