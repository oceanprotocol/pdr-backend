<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Run local agents, many processes (one per agent)

### Overview

In this step, you run and create agents.

In this README:
- agents live on your local machine
- each agent gets its own console / process

Prerequisites:
- [Installed pdr-backend](install.md)
- [Setup local chain](setup-local.md) or [remote chain](setup-remote.md)
- [Deployed DT3](deploy-dt3.md)


### Steps

Create 3 new terminals, for:

1. [trueval](#Terminal-1-trueval)
2. [predictoor](#Terminal-2-predictoor)
3. [trader](#Terminal-3-trader)


### Terminal 1: trueval

In bash console:
```console
# Setup env
cd pdr-backend
source venv/bin/activate

# Set envvars
export ADDRESS_FILE="${HOME}/.ocean/ocean-contracts/artifacts/address.json"
export RPC_URL=http://127.0.0.1:8545
export SUBGRAPH_URL="http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph"
export PRIVATE_KEY="0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58"

# Run
python3 pdr_backend/trueval/main.py
```


### Terminal 2: predictoor

In bash console:
```console
# Setup env
cd pdr-backend
source venv/bin/activate

# Set envvars
export ADDRESS_FILE="${HOME}/.ocean/ocean-contracts/artifacts/address.json"
export RPC_URL=http://127.0.0.1:8545
export SUBGRAPH_URL="http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph"
export PRIVATE_KEY="0xef4b441145c1d0f3b4bc6d61d29f5c6e502359481152f869247c7a4244d45209"

# Run
python3 pdr_backend/predictoor/main.py
```

### Terminal 3: trader

In bash console:
```console
# Setup env
cd pdr-backend
source venv/bin/activate

# Set envvars
export ADDRESS_FILE="${HOME}/.ocean/ocean-contracts/artifacts/address.json"
export RPC_URL=http://127.0.0.1:8545
export SUBGRAPH_URL="http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph"
export PRIVATE_KEY="0x8467415bb2ba7c91084d932276214b11a3dd9bdb2930fefa194b666dd8020b99"

# Run
python3 pdr_backend/trader/main.py
```

