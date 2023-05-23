#!/bin/bash

# Constants
KAFKA_CLUSTER_ID=$(curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/attributes/KAFKA_CLUSTER_ID)
NODE_ID=$(curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/attributes/NODE_ID)
EXTERNAL_IP=$(curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip)

ip_addresses=()
for i in {1..3}; do
  address_name="kafka-controller-$i"
  region="us-central1"
  address=$(gcloud compute addresses describe "$address_name" --region="$region" --format='get(address)')
  ip_addresses+=("$address")
done

urls=()
for (( i=1; i<=${#ip_addresses[@]}; i++ ))
do
  url="${i}@${ip_addresses[$i-1]}:9093"
  urls+=("$url")
done

CONTROLLER_QUORUM_VOTERS=$(IFS=','; echo "${urls[*]}")

echo "NODE_ID: $NODE_ID"
echo "KAFKA_CLUSTER_ID: $KAFKA_CLUSTER_ID"
echo "CONTROLLER_QUORUM_VOTERS: $CONTROLLER_QUORUM_VOTERS"
echo "EXTERNAL_IP: $EXTERNAL_IP"


echo "Installing java"

sudo rm -rf /var/lib/man-db/auto-update
sudo apt-get -qq update
sudo apt-get -qq install -y default-jdk


echo "Downloading Kafka"

cd /opt
sudo curl https://downloads.apache.org/kafka/3.4.0/kafka_2.13-3.4.0.tgz -o kafka.tgz
sudo tar -xzf kafka.tgz
sudo mv kafka_2.13-3.4.0/ kafka/
sudo rm -rf kafka.tgz
cd kafka


echo "Configuring Kafka"

sudo mkdir /var/log/kafka
sudo chown -R $USER:$USER /var/log/kafka

sudo sed -i "s|log.dirs=.*|log.dirs=/var/log/kafka|g" config/kraft/server.properties
sudo sed -i "s|listeners=.*|listeners=PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093|g" config/kraft/server.properties
sudo sed -i "s|advertised.listeners=.*|advertised.listeners=PLAINTEXT://$EXTERNAL_IP:9092|g" config/kraft/server.properties
sudo sed -i "s|node.id=.*|node.id=$NODE_ID|g" config/kraft/server.properties
sudo sed -i "s|controller.quorum.voters=.*|controller.quorum.voters=$CONTROLLER_QUORUM_VOTERS|g" config/kraft/server.properties

sudo bin/kafka-storage.sh format -t $KAFKA_CLUSTER_ID -c config/kraft/server.properties

echo "Finished configuring Kafka properties"


# Create systemd service file
cat << EOF | sudo tee /etc/systemd/system/kafka.service
[Unit]
Description=Apache Kafka Server
Documentation=http://kafka.apache.org/documentation.html
Requires=network.target remote-fs.target
After=network.target remote-fs.target

[Service]
Type=simple
ExecStart=/opt/kafka/bin/kafka-server-start.sh /opt/kafka/config/kraft/server.properties
ExecStop=/opt/kafka/bin/kafka-server-stop.sh
Restart=on-abnormal
User=root
Group=root

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd to recognize Kafka
sudo systemctl daemon-reload
# Start Kafka service
sudo systemctl start kafka
# Enable Kafka service to start on boot
sudo systemctl enable kafka

echo "Kafka server started"
