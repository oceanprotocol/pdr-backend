#!/bin/bash

# install pm2
sudo apt install npm
sudo npm install pm2@latest -g

# Change directory to pdr-backend
cd /home/${var.username}/pdr-backend

# Download config files from GCS bucket
gsutil cp ${google_storage_bucket_object.pm2_config_file_5m.name} /home/${var.username}/pdr-backend/scripts/terraform/pm2-config/mainnet-predictoor-5m.config.js
gsutil cp ${google_storage_bucket_object.pm2_config_file_1h.name} /home/${var.username}/pdr-backend/scripts/terraform/pm2-config/mainnet-predictoor-1h.config.js

# Define an array of feed names
feeds_5m=("BTC_5m" "ETH_5m" "ADA_5m" "BNB_5m" "SOL_5m" "XRP_5m" "DOT_5m" "LTC_5m" "DOGE_5m" "TRX_5m")
feeds_1h=("BTC_1h" "ETH_1h" "ADA_1h" "BNB_1h" "SOL_1h" "XRP_1h" "DOT_1h" "LTC_1h" "DOGE_1h" "TRX_1h")

# Iterate over 5m feed names and export the corresponding private keys
for feed in "${feeds_5m[@]}"; do
  export "${feed}_PK=${var."${feed}_PK"}"
done

# Iterate over 1h feed names and export the corresponding private keys
for feed in "${feeds_1h[@]}"; do
  export "${feed}_PK=${var."${feed}_PK"}"
done

# Run PM2 for all feeds
pm2 start /home/${var.username}/pdr-backend/scripts/terraform/pm2-config/mainnet-predictoor-5m.config.js
pm2 start /home/${var.username}/pdr-backend/scripts/terraform/pm2-config/mainnet-predictoor-1h.config.js
