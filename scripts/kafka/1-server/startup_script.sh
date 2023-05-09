#!/bin/bash

echo "Installing java"

sudo apt-get -qq update
sudo apt-get install -y default-jdk


cd /home
echo "Downloading Kafka"

curl https://downloads.apache.org/kafka/3.4.0/kafka_2.13-3.4.0.tgz -o kafka_2.13-3.4.0.tgz
tar -xzf kafka_2.13-3.4.0.tgz
sudo rm -rf kafka_2.13-3.4.0.tgz
cd kafka_2.13-3.4.0


EXTERNAL_IP=$(curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip)
echo "External IP Address: $EXTERNAL_IP"


echo "Configuring Kafka"
sudo mkdir /var/lib/kafka
sudo mkdir /var/lib/kafka/logs
sudo chown -R $USER:$USER /var/lib/kafka

sudo sed -i 's|log.dirs=.*|log.dirs=/var/lib/kafka/logs|g' config/kraft/server.properties
sudo sed -i "s|advertised.listeners=.*|advertised.listeners=PLAINTEXT://$EXTERNAL_IP:9092|g" config/kraft/server.properties

KAFKA_CLUSTER_ID="$(bin/kafka-storage.sh random-uuid)"
sudo bin/kafka-storage.sh format -t $KAFKA_CLUSTER_ID -c config/kraft/server.properties

echo "Finished configuring Kafka properties"
cat config/kraft/server.properties


# Start Kafka
nohup sudo bin/kafka-server-start.sh config/kraft/server.properties > /dev/null 2>&1 &

echo "Kafka server started"
