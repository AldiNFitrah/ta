# This code is compatible with Terraform 4.25.0 and versions that are backwards compatible to 4.25.0.
# For information about validating this Terraform code, see https://developer.hashicorp.com/terraform/tutorials/gcp-get-started/google-cloud-platform-build#format-and-validate-the-configuration

resource "google_compute_address" "kafka-controller" {
  project = "sonic-totem-383508"
  count = 3
  name  = "kafka-controller-${count.index + 1}"
  region = "us-central1"
}

resource "google_compute_instance" "kafka-kraft-3servers-v1" {
  project = "sonic-totem-383508"
  count = 3

  boot_disk {
    auto_delete = true
    device_name = "kafka-kraft-3servers-v1-${count.index + 1}"

    initialize_params {
      image = "projects/debian-cloud/global/images/debian-11-bullseye-v20230509"
      size  = 10
      type  = "pd-balanced"
    }
  }

  labels = {
    ec-src = "vm_add-tf"
  }

  machine_type = "n1-standard-1"

  metadata = {
    KAFKA_CLUSTER_ID = "7Uu4ZfOySeKnsA28hjECaQ"
    NODE_ID          = count.index + 1
    startup-script   = "#!/bin/bash\n\n# Constants\nKAFKA_CLUSTER_ID=$(curl -H \"Metadata-Flavor: Google\" http://metadata.google.internal/computeMetadata/v1/instance/attributes/KAFKA_CLUSTER_ID)\nNODE_ID=$(curl -H \"Metadata-Flavor: Google\" http://metadata.google.internal/computeMetadata/v1/instance/attributes/NODE_ID)\nEXTERNAL_IP=$(curl -H \"Metadata-Flavor: Google\" http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip)\n\nip_addresses=()\nfor i in {1..3}; do\n  address_name=\"kafka-controller-$i\"\n  region=\"us-central1\"\n  address=$(gcloud compute addresses describe \"$address_name\" --region=\"$region\" --format='get(address)')\n  ip_addresses+=(\"$address\")\ndone\n\nurls=()\nfor (( i=1; i<=$${#ip_addresses[@]}; i++ ))\ndo\n  url=\"$${i}@$${ip_addresses[$i-1]}:9093\"\n  urls+=(\"$url\")\ndone\n\nCONTROLLER_QUORUM_VOTERS=$(IFS=','; echo \"$${urls[*]}\")\n\necho \"NODE_ID: $NODE_ID\"\necho \"KAFKA_CLUSTER_ID: $KAFKA_CLUSTER_ID\"\necho \"CONTROLLER_QUORUM_VOTERS: $CONTROLLER_QUORUM_VOTERS\"\necho \"EXTERNAL_IP: $EXTERNAL_IP\"\n\n\necho \"Installing java\"\n\nsudo rm -rf /var/lib/man-db/auto-update\nsudo apt-get -qq update\nsudo apt-get -qq install -y default-jdk\n\n\necho \"Downloading Kafka\"\n\ncd /opt\nsudo curl https://downloads.apache.org/kafka/3.4.0/kafka_2.13-3.4.0.tgz -o kafka.tgz\nsudo tar -xzf kafka.tgz\nsudo mv kafka_2.13-3.4.0/ kafka/\nsudo rm -rf kafka.tgz\ncd kafka\n\n\necho \"Configuring Kafka\"\n\nsudo mkdir /var/log/kafka\nsudo chown -R $USER:$USER /var/log/kafka\n\nsudo sed -i \"s|log.dirs=.*|log.dirs=/var/log/kafka|g\" config/kraft/server.properties\nsudo sed -i \"s|listeners=.*|listeners=PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093|g\" config/kraft/server.properties\nsudo sed -i \"s|advertised.listeners=.*|advertised.listeners=PLAINTEXT://$EXTERNAL_IP:9092|g\" config/kraft/server.properties\nsudo sed -i \"s|node.id=.*|node.id=$NODE_ID|g\" config/kraft/server.properties\nsudo sed -i \"s|controller.quorum.voters=.*|controller.quorum.voters=$CONTROLLER_QUORUM_VOTERS|g\" config/kraft/server.properties\n\nsudo bin/kafka-storage.sh format -t $KAFKA_CLUSTER_ID -c config/kraft/server.properties\n\necho \"Finished configuring Kafka properties\"\n\n\n# Create systemd service file\ncat << EOF | sudo tee /etc/systemd/system/kafka.service\n[Unit]\nDescription=Apache Kafka Server\nDocumentation=http://kafka.apache.org/documentation.html\nRequires=network.target remote-fs.target\nAfter=network.target remote-fs.target\n\n[Service]\nType=simple\nExecStart=/opt/kafka/bin/kafka-server-start.sh /opt/kafka/config/kraft/server.properties\nExecStop=/opt/kafka/bin/kafka-server-stop.sh\nRestart=on-abnormal\nUser=root\nGroup=root\n\n[Install]\nWantedBy=multi-user.target\nEOF\n\n# Reload systemd to recognize Kafka\nsudo systemctl daemon-reload\n# Start Kafka service\nsudo systemctl start kafka\n# Enable Kafka service to start on boot\nsudo systemctl enable kafka\n\necho \"Kafka server started\"\n"
  }

  name = "kafka-kraft-3servers-v1-${count.index + 1}"

  network_interface {
    access_config {
      nat_ip       = google_compute_address.kafka-controller[count.index].address
    }

    subnetwork = "projects/sonic-totem-383508/regions/us-central1/subnetworks/default"
  }

  service_account {
    email  = "976896726169-compute@developer.gserviceaccount.com"
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }

  tags = ["http-server", "https-server"]
  zone = "us-central1-a"
}
