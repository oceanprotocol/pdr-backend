<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Local Setup

We assume you've already [installed pdr-backend](install.md).

## 1. Download barge and run services

In a new console:

```console
# Grab repo
git clone https://github.com/oceanprotocol/barge
cd barge

# Clean up old containers (to be sure)
docker system prune -a --volumes

# Run barge: start Ganache. Choose specific Ocean Predictoor contrats
./start_ocean.sh --new-predictoor
```

Now that we have barge running, we can mostly ignore its console while it runs.

## 2. Set envvars

From here on, go to a console different than Barge. (E.g. the console where you installed Ocean, or a new one.)

First, ensure that you're in the working directory, with venv activated:

```console
cd pdr-utils
source venv/bin/activate
```

Then, set envvars.
```console
# keys for Alice and Bob in READMEs
export TEST_PRIVATE_KEY1=0x8467415bb2ba7c91084d932276214b11a3dd9bdb2930fefa194b666dd8020b99
export TEST_PRIVATE_KEY2=0x1d751ded5a32226054cd2e71261039b65afb9ee1c746d055dd699b1150a5befc

# needed by trueval, predictoor, trader
export ADDRESS_FILE="${HOME}/.ocean/ocean-contracts/artifacts/address.json"
export RPC_URL=http://127.0.0.1:8545
export SUBGRAPH_URL="http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph"
export PRIVATE_KEY=0x8467415bb2ba7c91084d932276214b11a3dd9bdb2930fefa194b666dd8020b99

# needed just by predictoor
export STAKE_AMOUNT=1 # maximum stake (in decimal) for each prediction

# private keys from barge
export OPF_DEPLOYER_PRIVATE_KEY=0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58
export PREDICTOOR_PRIVATE_KEY=0xef4b441145c1d0f3b4bc6d61d29f5c6e502359481152f869247c7a4244d45209
export TRADER_PRIVATE_KEY=0x8467415bb2ba7c91084d932276214b11a3dd9bdb2930fefa194b666dd8020b99
```
