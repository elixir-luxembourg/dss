# Elixir Data Submission System (DSS) Deployment


## Install platform dependencies

```bash
sudo yum install -y epel-release 
sudo yum group install -y "Development Tools"
sudo yum install -y nginx 
sudo yum install -y python36-devel   
sudo yum install -y java-1.8.0-openjdk-devel
sudo yum install -y supervisor  
curl "https://bootstrap.pypa.io/get-pip.py" | sudo python3.6   
```

### Install wkhtmltopdf
```bash
sudo yum install -y xorg-x11-fonts-Type1 xorg-x11-fonts-75dpi libjpeg-turbo libX11 libXext libXrender libpng
wget https://downloads.wkhtmltopdf.org/0.12/0.12.5/wkhtmltox-0.12.5-1.centos7.x86_64.rpm
rpm -Uvh wkhtmltox-0.12.5-1.centos7.x86_64.rpm
```

## Create elixirdcp user and clone project
```bash
sudo useradd elixirdcp
sudo passwd elixirdcp
su - elixirdcp
```
#### Setup folder structure
```
mkdir app-data
mkdir app-src
mkdir app-data/uploads
mkdir app-data/exports
mkdir app-logs
```

#### Clone project and set secret
```bash
cd app-src
git clone ssh://git@git-r3lab-server.uni.lu:8022/elixir/elixir-dcp.git
```

Put in the client id and client secret:

```bash
cd elixir-dcp
vi elixir_dcp/client_secrets.json
```

## Install

### Setup virtual environment

```bash
mkdir project_venv
```

Create the environment using venv module

```bash
python3.6 -m venv project_venv
```

<font style="color:grey">If previous command fails (e.g. on CentOS), run "`sudo pip install virtualenv`" and create environment as elixirdcp user by running "`virtualenv --python=$(which python3.6) project_venv`"</font>

Finally, activate virtual environment and install dependencies:

```bash
source project_venv/bin/activate
pip install -e .
pip install gunicorn
```

## Configure Project

```bash
cp elixir_dcp/settings.py.template elixir_dcp/settings.py
```

Edit settings.py as necessary. Set `ELIXIR_DCP_ENV` to 'prod'.

Initialize the database to add the admin user and basic lookup values.

```bash
python3.6 manage.py init_db
```

## Configure and run nginx

```bash
# if it does not already exist
sudo mkdir /etc/nginx/conf.d
# create symlink
sudo ln -s /home/elixirdcp/app-src/elixir-dcp/deploy/elixir-dcp-nginx.conf /etc/nginx/conf.d/elixir-dcp-nginx.conf
sudo vi /etc/nginx/nginx.conf
```

Change nginx.conf so that:

1. comment out the  `server {...}` section.

2. nginx is being run with the elixirdcp user.

    ```config
    user elixirdcp;
    ```

3. Ensure that elixir-dcp's nginx conf file is included as follows
  
    ```config
    http {
      # ... ...
      # ... ... nginx stuff
      # ... ...
      # include all server conf files
      include /etc/nginx/conf.d/*.conf;
    }
    ```

Create self-signed certificates if they already don't exist.

```bash
cd /home/elixirdcp/app-src/elixir-dcp/deploy
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
```

Change ownership of nginx:

```bash
sudo chown -R elixirdcp.elixirdcp /var/lib/nginx
```

Start NGINX web server

```bash
systemctl enable nginx
systemctl start nginx
```

## Configure and run GUNICORN web application server

```bash
sudo ln -s /home/elixirdcp/app-src/elixir-dcp/deploy/elixir-dcp-gunicorn.ini  /etc/supervisord.d/elixir-dcp-gunicorn.ini
sudo systemctl start supervisord
sudo supervisorctl start gunicorn
```

Go to:  https://elixir-dcp.lcsb.uni.lu  to check if it works

## For Maintenance and Updates

```bash
sudo nginx -s stop
sudo supervisorctl stop gunicorn


git pull
pip install -e . --upgrade
cd elixir_dcp/static/vendor
npm ci


sudo supervisorctl start gunicorn
sudo nginx
```
