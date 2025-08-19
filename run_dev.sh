#!/bin/bash
source ./project_venv/bin/activate
export FLASK_APP=elixir_dcp
flask run --debug --port 5000