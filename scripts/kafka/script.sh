echo "Installing java . . ."
sudo apt update && sudo apt -y install default-jdk

echo "Downloading Kafka Binary . . ."
mkdir ~/downloads
curl "https://dlcdn.apache.org/kafka/3.4.0/kafka_2.13-3.4.0.tgz" -o ~/downloads/kafka.tgz
mkdir ~/kafka && cd ~/kafka
tar -xvzf ~/downloads/kafka.tgz --strip 1

export KAFKA_HOME="~/kafka"
export PATH="$KAFKA_HOME/bin:$PATH"

KAFKA_CLUSTER_ID="$(kafka-storage.sh random-uuid)"

kafka-storage.sh format -t $KAFKA_CLUSTER_ID -c ~/kafka/config/kraft/server.properties
# kafka-server-start.sh ~/kafka/config/kraft/server.properties

sudo systemctl start kafka
sudo systemctl enable kafka


# gcloud compute instances create instance-1 --project=sonic-totem-383508 --zone=us-central1-a --machine-type=c3-highcpu-4 --network-interface=network-tier=PREMIUM,nic-type=GVNIC,subnet=default --maintenance-policy=MIGRATE --provisioning-model=STANDARD --service-account=976896726169-compute@developer.gserviceaccount.com --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append --tags=http-server,https-server --create-disk=auto-delete=yes,boot=yes,device-name=instance-1,image=projects/debian-cloud/global/images/debian-11-bullseye-v20230306,mode=rw,size=10,type=projects/sonic-totem-383508/zones/us-central1-a/diskTypes/pd-balanced --no-shielded-secure-boot --shielded-vtpm --shielded-integrity-monitoring --labels=ec-src=vm_add-gcloud --reservation-affinity=any
