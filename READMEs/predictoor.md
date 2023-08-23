<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Usage for Predictoors

This is for predictoors - people who are running `predictoor` agents to submit individual predictions.

## Contents

- [Install](#install)
- [Local Usage](#local-usage)
- [Remote Testnet Usage](#remote-testnet-usage)
- [Remote Mainnet Usage](#remote-mainnet-usage)

## Install

First, [install pdr-backend](install.md).

Then, [install barge](barge.md#install-barge).

## Local Usage

In barge console:
```console
#run barge with all agents except predictoor
./start_ocean.sh --predictoor --with-pdr-trueval --with-pdr-trader --with-pdr-publisher --with-pdr-dfbuyer
```

Open a new console and:
```
# Setup virtualenv
cd pdr-backend
source venv/bin/activate

# Set envvars
export ADDRESS_FILE="${HOME}/.ocean/ocean-contracts/artifacts/address.json"
export RPC_URL=http://127.0.0.1:8545
export SUBGRAPH_URL="http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph"
export PRIVATE_KEY="0xef4b441145c1d0f3b4bc6d61d29f5c6e502359481152f869247c7a4244d45209"
```

### Option A: Use Random Predictions

In the same console:
```
# run predictoor agent
python3 pdr_backend/predictoor/main.py
```

Relax & watch as the predictoor agent submits random predictions, trueval submits random true_vals for each epoch and trader signals trades.

You can query predictoor subgraph for detailed run info. See [subgraph.md](subgraph.md) for details.

The agent predicts according to the `predict()` function in [`pdr_backend/predictoor/predict.py`](../pdr_backend/predictoor/predict.py). Its default strategy is simplistic (random predictions). So you need to customize it. The docstring at the top of `predict.py` provides more info.

### Option B: Use Simple or Custom Model

- Clone the simple model [repo](https://github.com/oceanprotocol/pdr-model-simple) or fork the repo and create a custom model 
- From pdr-backend, make a symlink to the repo subdirectory for the simple model (or your own customized model) e.g. `ln -s /path/to/pdr-model-simple/pdr_model_simple/ pdr_backend/predictoor/examples/models`

In the same console:
```
# run predictoor agent
python3 pdr_backend/predictoor/examples/models/main.py
```

## Remote Testnet Usage

To run predictoor as azure container: see [azure-container-deployment.md](azure-container-deployment.md)

To get tokens from testnet: see [testnet-faucet.md](testnet-faucet.md)

## Remote Mainnet Usage

FIXME

