#!/bin/bash
set -e

# Install UV if not already installed
command -v uv >/dev/null 2>&1 || pip install uv

# Create venv and install dependencies with UV (matches CI: lockfile-enforced)
uv sync --locked --extra dev --extra test
source ./.venv/bin/activate
cd elixir_dss/static/vendor && npm ci && npm run build:css && cd ../../../
[ -f ".env.template" ] && [ ! -f ".env" ] && cp .env.template .env
./manage.py init-db
./manage.py load-demo-users
echo "Setup complete. Run ./run_dev.sh to start"
