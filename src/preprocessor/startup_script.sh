#!/bin/bash

# Install dependencies
sudo rm -rf /var/lib/man-db/auto-update
sudo apt-get -qq update
sudo apt-get install -y unzip python3-pip python3

# Clone repository
sudo curl -L -o app.zip https://github.com/AldiNFitrah/ta/archive/refs/heads/main.zip
sudo unzip app -d /opt
sudo rm -rf app.zip

cd /opt/ta-main
sudo chown -R $USER:$USER ./

# Install requirements
pip3 install -r requirements.txt

# Start application
nohup python3 main.py preprocess
