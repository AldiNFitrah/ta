#!/bin/bash

# Install dependencies
apt-get -qq update
apt-get install -y unzip python3-pip python3

# Clone repository
curl -L -o app.zip https://github.com/AldiNFitrah/ta/archive/refs/heads/main.zip
unzip app -d /opt
rm -rf app.zip

cd /opt/ta-main
sudo chown -R $USER:$USER ./

# Install requirements
pip3 install -r requirements.txt

# Start application
nohup python3 -m uvicorn src.server.main:app --host 0.0.0.0 &
