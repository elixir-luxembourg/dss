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

cd "$APP_DIR"

echo "Fetching tags..."
git fetch --tags origin

if [ -n "$VERSION" ]; then
    if ! echo "$VERSION" | grep -Eq '^v[0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9._/+-]+)?$'; then
        echo "Error: VERSION '$VERSION' has invalid format. Should be in format 'v1.0.0' or 'v0.2.0-dev'."
        exit 1
    fi
else
    echo "No VERSION provided. Using latest stable tag..."
    VERSION=$(git tag --list | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -1)
    if [ -z "$VERSION" ]; then
        echo "Error: No version tags found"
        exit 1
    fi
    echo "Selected: $VERSION"
fi

if ! git show-ref --tags --quiet --verify "refs/tags/$VERSION"; then
    echo "Error: Tag $VERSION does not exist"
    echo "Available stable tags:"
    git tag --list | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -5
    exit 1
fi

echo "Checking out tag: $VERSION"
if ! git checkout "$VERSION"; then
    echo "Error: git checkout $VERSION failed"
    exit 1
fi

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

echo "✓ Deployment completed successfully (version: $VERSION)!"
