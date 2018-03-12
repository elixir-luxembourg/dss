# Elixir Data and Computing Platform (Elixir-DCP)
# Deployment Documentation

# Install platform dependencies

sudo yum group install "Development Tools" (will provide you with git among other things)
sudo yum install nginx (our web server)
sudo yum python36-devel.x86_64   (Python)
sudo yum install java-1.8.0-openjdk-devel
sudo yum install supervisor   (a tool to manage gunicorn app server)
curl "https://bootstrap.pypa.io/get-pip.py" | sudo python3.6   (Install pip)

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
wget "https://server/elixir-dcp-dist.zip"
unzip elixir-dcp-dist.zip
cd elixir-dcp


vi client-secrets.json to put it the client id and client secret

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
sudo ln -s /home/elixirdcp/app-src/elixir-dcp/deploy/elixir-dcp-nginx.conf ./elixir-dcp-nginx.conf

sudo vi /etc/nginx/nginx.conf
1. Make sure the following line exists the end 
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



Go to:  http://elixir-dcp.lcsb.uni.lu  to check if nginx is installed properly






 sudo lsof -i :8000  See who uses port 8000 on my machine this was smth called a pma_agent
 
 sudo kill -9 XXXXX kill that process
 
 
 

sudo supervisord -c supervisord.ini



 
TODO: 
set the  authorized URLs in ELIXIR AAI.

I had to do chmod 751 on /pinar_alper/Desktop/  to allow nginx serve the uploaded files..

add step for creating environment variable setting config to "prod"




 
 
 