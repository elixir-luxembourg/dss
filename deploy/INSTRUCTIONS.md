# LCSB DSS Deployment Guide

Deployment using systemd and nginx on Rocky Linux 8

## 1. Install System Dependencies

```bash
sudo dnf update -y
sudo dnf install -y python3.12 python3.12-pip nginx git nodejs npm
sudo dnf groupinstall -y "Development Tools"
```

## 2. Setup Application User

```bash
sudo useradd elixirdss

# Grant limited sudo access (only for deployment commands)
echo "elixirdss ALL=(ALL) NOPASSWD: /usr/bin/systemctl, /usr/bin/chmod, /usr/bin/chown, /usr/bin/ln" | sudo tee /etc/sudoers.d/elixirdss
sudo chmod 440 /etc/sudoers.d/elixirdss

sudo su - elixirdss
```

Create directory structure:
```bash
mkdir -p app-src app-data/{uploads,exports} app-logs
```

Setup SSH key for private repository access:
```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "elixirdss-deploy"

# Display public key to add to GitHub Deploy Keys
cat ~/.ssh/id_ed25519.pub
# Add this key to: GitHub repo → Settings → Deploy keys → Add deploy key
```

Clone repository:
```bash
cd app-src
git clone git@github.com:elixir-luxembourg/dss.git elixir-dss
cd elixir-dss
```

## 3. Configure Application

```bash
# Create virtual environment
python3.12 -m venv project_venv
source project_venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -e .
pip install gunicorn

# Build frontend assets
cd elixir_dss/static/vendor
npm ci
npm run build:css
cd ../../..

# Configure environment
cp .env.template .env
vi .env  # Set ELIXIR_DSS_ENV=prod

# Install LFT client
cd ~/app-src/elixir-dss/
git clone git@gitlab.com:uniluxembourg/lcsb/elixir/lft/lftpythonclient.git
pip install -e .
cd ..

# Initialize database
./manage.py init-db
./manage.py load-demo-users
```

## 4. Setup Systemd Service

```bash
sudo ln -s /home/elixirdss/app-src/elixir-dss/deploy/elixir-dss-gunicorn.ini \
           /etc/systemd/system/elixir-dss.service

sudo systemctl daemon-reload
sudo systemctl enable elixir-dss
sudo systemctl start elixir-dss
```

## 5. Configure Nginx

Create SSL certificates (if needed):
```bash
cd /home/elixirdss/app-src/elixir-dss/deploy
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
```

Setup nginx:
```bash
sudo ln -s /home/elixirdss/app-src/elixir-dss/deploy/elixir-dss-nginx.conf \
           /etc/nginx/conf.d/elixir-dss.conf
```

### Fix static file permissions for nginx
If you see nginx errors like `Permission denied` for static files, run the following commands to ensure nginx can traverse directories and read static files:

```bash
# Make directories traversable and files readable by nginx
sudo chmod 755 /home/elixirdss
sudo chmod 755 /home/elixirdss/app-src
sudo chmod 755 /home/elixirdss/app-src/elixir-dss
sudo chmod 755 /home/elixirdss/app-src/elixir-dss/elixir_dss
sudo chmod 755 /home/elixirdss/app-src/elixir-dss/elixir_dss/static
sudo chmod -R 755 /home/elixirdss/app-src/elixir-dss/elixir_dss/static/public
sudo chmod -R +r /home/elixirdss/app-src/elixir-dss/elixir_dss/static/public
```

Continue with nginx setup:
```bash
sudo chown -R nginx:nginx /var/lib/nginx
sudo systemctl enable nginx
sudo systemctl restart nginx
```

## Maintenance

### Update Application
```bash
su - elixirdss
cd ~/app-src/elixir-dss

git fetch --tags origin
git checkout v0.1.2

source project_venv/bin/activate
pip install -e . --upgrade
cd elixir_dss/static/vendor
npm ci
npm run build:css
exit

sudo systemctl restart elixir-dss
sudo systemctl restart nginx
```

### Update with .sh
```bash
sudo bash /home/elixirdss/app-src/elixir-dss/update_release.sh v0.1.2
```

### View Logs
```bash
# Application logs
tail -f /home/elixirdss/app-logs/gunicorn-error.log

# Nginx logs
tail -f /var/log/nginx/error.log
```

### Check Status
```bash
sudo systemctl status elixir-dss
sudo systemctl status nginx
```

Access at: https://dss-elixir-srv.lcsb.uni.lu/
