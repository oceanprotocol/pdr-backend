# Configure the cloud provider
provider "google" {
  credentials = file(var.credentials_path)  # Replace with your GCP credentials file
  project     = var.project_id             # Replace with your GCP project ID
  region      = "europe-west4"                    # Replace with your desired region
}

resource "google_compute_instance" "vm_instance" {
  name         = "predictoor-vm"                   # Replace with your desired VM name
  machine_type = "n2-standard-4"                  # Replace with your desired machine type
  zone         = "europe-west4-a"                 # Replace with your desired zone

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2004-lts"   # Replace with your desired OS image
      size  = 100                                # Replace with your desired disk size in GB
    }
  }
  
  network_interface {
    network = "default"
    access_config {
      # Ephemeral IP
    }
  }
  
  metadata_startup_script = <<-EOF
    #!/bin/bash

    # Create path for ocean-contracts and clone contract address list
    mkdir /home/${var.username}/.ocean/
    mkdir /home/${var.username}/.ocean/ocean-contracts/
    mkdir /home/${var.username}/.ocean/ocean-contracts/artifacts/
    wget https://github.com/idiom-bytes/predictoor_contracts/raw/main/address.json -O /home/${var.username}/.ocean/ocean-contracts/artifacts/address.json

    # Install Git
    sudo apt-get update
    sudo apt-get install -y git

    # Clone the GitHub repository
    git clone https://github.com/oceanprotocol/pdr-backend.git /home/${var.username}/pdr-backend

    # Change directory to pdr-backend
    cd /home/${var.username}/pdr-backend
    git checkout ${var.predictoor_branch}

    # Install Python 3 venv
    sudo apt-get install -y python3-venv

    # Create a virtual environment and install requirements
    python3 -m venv venv
    source ./venv/bin/activate
    pip install -r requirements.txt

    # export 5m PKs 
    export BTC_5m_PK=${var.BTC_5m_PK}
    export ETH_5m_PK=${var.ETH_5m_PK}
    export ADA_5m_PK=${var.ADA_5m_PK}
    export BNB_5m_PK=${var.BNB_5m_PK}
    export SOL_5m_PK=${var.SOL_5m_PK}
    export XRP_5m_PK=${var.XRP_5m_PK}
    export DOT_5m_PK=${var.DOT_5m_PK}
    export LTC_5m_PK=${var.LTC_5m_PK}
    export DOGE_5m_PK=${var.DOGE_5m_PK}
    export TRX_5m_PK=${var.TRX_5m_PK}

    # export 1h PKs 
    export BTC_1h_PK=${var.BTC_1h_PK}
    export ETH_1h_PK=${var.ETH_1h_PK}
    export ADA_1h_PK=${var.ADA_1h_PK}
    export BNB_1h_PK=${var.BNB_1h_PK}
    export SOL_1h_PK=${var.SOL_1h_PK}
    export XRP_1h_PK=${var.XRP_1h_PK}
    export DOT_1h_PK=${var.DOT_1h_PK}
    export LTC_1h_PK=${var.LTC_1h_PK}
    export DOGE_1h_PK=${var.DOGE_1h_PK}
    export TRX_1h_PK=${var.TRX_1h_PK}

    # Run PM2 for all feeds
    pm2 start /home/${var.username}/pdr-backend/scripts/terraform/pm2-config/mainnet-predictoor-5m.config.js
    pm2 start /home/${var.username}/pdr-backend/scripts/terraform/pm2-config/mainnet-predictoor-1h.config.js
  EOF
}

output "external_ip" {
  value = google_compute_instance.vm_instance.network_interface[0].access_config[0].nat_ip
}