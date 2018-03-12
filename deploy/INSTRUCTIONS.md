# Elixir Data and Computing Platform (Elixir-DCP)
# Deployment Documentation

# Install platform dependencies

sudo yum group install "Development Tools" 
sudo yum install nginx 
sudo yum python36-devel.x86_64   
sudo yum install java-1.8.0-openjdk-devel
sudo yum install supervisor  
curl "https://bootstrap.pypa.io/get-pip.py" | sudo python3.6   

# Create elixirdcp user 
sudo useradd elixirdcp
sudo passwd elixirdcp
su elixirdcp

mkdir app-data
mkdir app-data/uploads
mkdir app-src
mkdir app-logs

# Get the project
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

# Configure And Run project with Gunicore

cp elixir_dcp/settings.py.template elixir_dcp/settings.py
/Users/pinar_alper/Work/biocore-repos/elixir-dcp/project_venv/bin/gunicorn elixir_dcp:app

# Configure and run nginx 

sudo mkdir /etc/nginx/conf.d  (if it does not already exist)
sudo ln -s /home/elixirdcp/app-src/elixir-dcp/deploy/elixir-dcp-nginx.conf /etc/nginx/conf.d/elixir-dcp-nginx.conf

sudo vi /etc/nginx/nginx.conf
1. Make sure the following line exists 
        http {
          # ... ...
          # ... ... nginx stuff
          # ... ...
          
          # include all server conf files
          include conf.d/*.conf;
        }
2. change the user for running nginx to elixirdcp

sudo nginx # starts web server
sudo nginx -s stop #stops web server


sudo ln -s /home/elixirdcp/app-src/elixir-dcp/deploy/elixir-dcp-gunicorn.ini  /etc/supervisord.d/elixir-dcp-gunicorn.ini
sudo systemctl start supervisord


Go to:  http://elixir-dcp.lcsb.uni.lu  to check if it works


 
TODO: 

I had to do chmod 751 on upload folder  to allow nginx serve the  files.

supervior gunicorn config set environment variable setting config to "prod"




 
 
 