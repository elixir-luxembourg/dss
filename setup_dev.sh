#!/bin/bash
set -e

# Install UV if not already installed
command -v uv >/dev/null 2>&1 || pip install uv

# Create venv and install dependencies with UV
uv venv project_venv
source ./project_venv/bin/activate
uv pip install -e '.[dev]'
cd elixir_dss/static/vendor && npm ci && npm run build:css && cd ../../../
[ -f ".env.template" ] && [ ! -f ".env" ] && cp .env.template .env
./manage.py init-db
./manage.py load-demo-users
echo "Setup complete. Run ./run_dev.sh to start"
