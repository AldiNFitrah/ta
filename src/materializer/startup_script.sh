#!/bin/bash

# Install dependencies
sudo rm -rf /var/lib/man-db/auto-update
sudo apt-get -qq update
sudo apt-get install -y python3-pip python3 git


# Clone repository
sudo mkdir /opt/ta
cd /opt/ta
sudo chown -R $USER:$USER ./

sudo git config --system --add safe.directory '*'
sudo git clone https://github.com/AldiNFitrah/ta.git .
sudo git pull origin main


# Install requirements
pip3 install -r requirements.txt --system --no-cache-dir --no-warn-script-location


# Start application
nohup python3 -m src.materializer.main
