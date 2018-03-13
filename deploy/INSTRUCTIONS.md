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
## Create elixirdcp user 
```bash
sudo useradd elixirdcp
sudo passwd elixirdcp
su elixirdcp

mkdir app-data
mkdir app-data/uploads
mkdir app-src
mkdir app-logs
```

## Get the project
```bash
cd app-src
git clone ssh://git@git-r3lab-server.uni.lu:8022/elixir/elixir-dcp.git
cd elixir-dcp


vi client-secrets.json 
(put in the client id and client secret)

mkdir project_venv
python3.6 -m venv project_venv
source project_venv/bin/activate

pip install -e .
pip install gunicorn

```
## Configure And Run project with Gunicore
```bash
cp elixir_dcp/settings.py.template elixir_dcp/settings.py
/Users/pinar_alper/Work/biocore-repos/elixir-dcp/project_venv/bin/gunicorn elixir_dcp:app
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

Start NGINX web server
```bash
sudo nginx 
```

Start GUNICORN web application server
```bash
sudo ln -s /home/elixirdcp/app-src/elixir-dcp/deploy/elixir-dcp-gunicorn.ini  /etc/supervisord.d/elixir-dcp-gunicorn.ini
sudo systemctl start supervisord
```
Fix needed for file uploads to work

sudo chown -R elixirdcp.elixirdcp /var/lib/nginx

Go to:  http://elixir-dcp.lcsb.uni.lu  to check if it works


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



 
 
 