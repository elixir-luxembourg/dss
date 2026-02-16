#!/bin/bash
set -e

APP_DIR="/home/elixirdss/app-src/elixir-dss"

# If not running as elixirdss user, switch to it
if [ "$USER" != "elixirdss" ]; then
    echo "Switching to elixirdss user..."
    exec sudo -u elixirdss bash "$0" "$@"
fi

VERSION="${1}"

echo "=== Deploying Elixir DSS ==="
echo "Started at: $(date)"

cd "$APP_DIR"

echo "Fetching tags..."
git fetch --tags origin

if [ -z "$VERSION" ]; then
    echo "No VERSION provided. Using latest stable tag..."
    VERSION=$(git tag | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -1)
    if [ -z "$VERSION" ]; then
        echo "Error: No version tags found"
        exit 1
    fi
    echo "Selected: $VERSION"
fi

if ! git rev-parse "$VERSION" >/dev/null 2>&1; then
    echo "Error: Tag $VERSION does not exist"
    echo "Available tags:"
    git tag --list | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -5
    exit 1
fi

echo "Checking out tag: $VERSION"
git checkout "$VERSION"

echo "Updating Python dependencies..."
source project_venv/bin/activate
pip install -e . --upgrade

echo "Applying database migrations..."
flask db upgrade

echo "Building frontend assets..."
cd elixir_dss/static/vendor
npm ci
npm run build:css

echo "Restarting services..."
sudo systemctl restart elixir-dss
sudo systemctl restart nginx

echo "✓ Deployment completed successfully!"
echo "✓ Deployed version: $VERSION"
