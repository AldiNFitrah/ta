#!/bin/bash

# Install dependencies
sudo rm -rf /var/lib/man-db/auto-update
sudo apt-get -qq update
sudo apt-get install -y python3-pip python3 git

# Clone repository
sudo mkdir /opt/ta
cd /opt/ta
sudo git clone https://github.com/AldiNFitrah/ta.git .
sudo git pull origin main

sudo chown -R $USER:$USER ./

# Install requirements
pip3 install -r requirements.txt

# Start application
nohup python3 -m uvicorn src.server.main:app --host 0.0.0.0 &
