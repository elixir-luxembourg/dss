# Elixir Data and Computing Platform (elixir-dcp) Deployment


## Install platform dependencies

```bash
sudo yum group install "Development Tools" 
sudo yum install nginx 
sudo yum python36-devel.x86_64   
sudo yum install java-1.8.0-openjdk-devel
sudo yum install supervisor  
curl "https://bootstrap.pypa.io/get-pip.py" | sudo python3.6   
```

##Install wkhtmltopdf
```bash
yum install xorg-x11-fonts-Type1 xorg-x11-fonts-75dpi libjpeg-turbo libX11 libXext libXrender libpng
wget https://downloads.wkhtmltopdf.org/0.12/0.12.5/wkhtmltox-0.12.5-1.centos7.x86_64.rpm
rpm -Uvh wkhtmltox-0.12.5-1.centos7.x86_64.rpm
```

## Create elixirdcp user 
```bash
sudo useradd elixirdcp
sudo passwd elixirdcp
su elixirdcp

mkdir app-data
mkdir app-src
mkdir app-data/uploads
mkdir app-data/exports
mkdir app-logs
```

## Get the project
```bash
cd app-src
git clone ssh://git@git-r3lab-server.uni.lu:8022/elixir/elixir-dcp.git
cd elixir-dcp


vi elixir_dcp/client_secrets.json 
(put in the client id and client secret)

mkdir project_venv
python3.6 -m venv project_venv
source project_venv/bin/activate

pip install -e .
pip install gunicorn

```
## Configure Project
```bash
export ELIXIR_DCP_ENV="prod"
cp elixir_dcp/settings.py.template elixir_dcp/settings.py
elixir-dcp/manage.py init_db
```


## Configure and run nginx 
```bash
sudo mkdir /etc/nginx/conf.d  (if it does not already exist)
sudo ln -s /home/elixirdcp/app-src/elixir-dcp/deploy/elixir-dcp-nginx.conf /etc/nginx/conf.d/elixir-dcp-nginx.conf
sudo vi /etc/nginx/nginx.conf
```
Change nginx.conf so that:

1- comment out the  server {...} section.

2- nginx is being run with the elixirdcp user.
```config
user elixirdcp;
```
3- elixir-dcp's nginx conf file is included as follows

```config
        http {
          # ... ...
          # ... ... nginx stuff
          # ... ...
          
          # include all server conf files
          include conf.d/*.conf;
        }
```

Create self-signed certificates if they already don't exist.
```bash
cd /home/elixirdcp/app-src/elixir-dcp/deploy
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
```

Start NGINX web server
```bash
sudo nginx 
```

## Configure and run GUNICORN web application server 
```bash
sudo ln -s /home/elixirdcp/app-src/elixir-dcp/deploy/elixir-dcp-gunicorn.ini  /etc/supervisord.d/elixir-dcp-gunicorn.ini
sudo systemctl start supervisord
sudo supervisorctl start gunicorn
```
Fix needed for file uploads to work
```bash
sudo chown -R elixirdcp.elixirdcp /var/lib/nginx
```

Go to:  https://elixir-dcp.lcsb.uni.lu  to check if it works


Initialize the database to add the admin user and basic lookup values.

```bash
./manage.py init_db
```

## For Maintenance and Updates
```bash
sudo nginx -s stop 
sudo supervisorctl stop gunicorn

git fetch --all
git reset --hard origin/master

...make necessary config changes...

sudo supervisorctl start gunicorn
sudo nginx 
```



 
 
 