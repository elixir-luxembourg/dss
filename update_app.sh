#!/bin/bash
set -e

APP_DIR="/home/elixirdss/app-src/elixir-dss"

# If not running as elixirdss user, switch to it
if [ "$USER" != "elixirdss" ]; then
    echo "Switching to elixirdss user..."
    exec sudo -u elixirdss bash "$0" "$@"
fi

echo "=== Updating Elixir DSS ==="

cd "$APP_DIR"
git checkout develop
git pull

# Update Python dependencies
source project_venv/bin/activate
pip install -e . --upgrade

# Build frontend assets
cd elixir_dss/static/vendor
npm ci
npm run build:css

# Restart services
sudo systemctl restart elixir-dss
sudo systemctl restart nginx

echo "✓ Update completed successfully!"
