#!/bin/bash
set -e

python3 -m venv project_venv
source ./project_venv/bin/activate
pip install -e .[dev]
cd elixir_dcp/static/vendor && npm ci && npm run build:css && cd ../../../
[ ! -f "elixir_dcp/settings.py" ] && cp ./elixir_dcp/settings.py.template elixir_dcp/settings.py
[ -f ".env.template" ] && [ ! -f ".env" ] && cp .env.template .env
export FLASK_APP=elixir_dcp
./manage.py init-db
./manage.py load-demo-users
echo "Setup complete. Run ./run_dev.sh to start"
