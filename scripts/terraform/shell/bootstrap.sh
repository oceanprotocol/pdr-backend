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
git checkout ${var.pdr_backend_branch}

# Install Python 3 venv
sudo apt-get install -y python3-venv

# Create a virtual environment and install requirements
python3 -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt