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

### Local Usage: Setup

In barge console:
```console
#run barge with all agents except predictoor
./start_ocean.sh --no-aquarius --no-elasticsearch --no-provider --no-dashboard --predictoor --with-thegraph --with-pdr-trueval --with-pdr-trader --with-pdr-publisher --with-pdr-dfbuyer
```

Open a new "work" console and:
```
# Setup virtualenv
cd pdr-backend
source venv/bin/activate

# Set envvars
export ADDRESS_FILE="${HOME}/.ocean/ocean-contracts/artifacts/address.json"
export RPC_URL=http://127.0.0.1:8545
export SUBGRAPH_URL="http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph"
export PRIVATE_KEY="0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58"
```

### Local Usage: Random (Approach 1)

To get started, let's run a predictoor agent with random predictions.

- The agent runs from [`predictoor/approach1/main.py`](../pdr_backend/predictoor/approach1/main.py)
- Which predicts according to the `predict()` function in [`predictoor/approach1/predict.py`](../pdr_backend/predictoor/approach1/predict.py) in the same dir.

In work console:
```console
# run random predictoor agent
python pdr_backend/predictoor/approach1/main.py
```

Observe the agents in action:
- In the barge console: trueval agent submitting (mock random) truevals, trader is (mock) trading, etc
- In your work console: predictoor agent is submitting (mock random) predictions

You can query predictoor subgraph for detailed run info. [`subgraph.md`](subgraph.md) has details.

### Local Usage: Model-based (Approach 2)

Since random predictions aren't accurate, let's use AI/ML models. Here's an example flow that loads pre-learned models ("approach2"):

- The agent runs from [`predictoor/approach2/main.py`](../pdr_backend/predictoor/approach2/main.py), using `predict.py` in the same dir.
- Which imports a model stored in [`pdr-model-simple`](https://github.com/oceanprotocol/pdr-model-simple) repo

Once you're familiar with this, you'll want to fork it and run your own.

In work console:
```console
# (ctrl-c existing run)

# go to a directory where you'll want to clone to. 
cd ..

#clone model repo
git clone https://github.com/oceanprotocol/pdr-model-simple

#the script below needs this envvar, to know where to import model.py from
export MODELDIR=$(pwd)/pdr-model-simple/

#pip install anything that pdr-model-simple/model.py needs
pip install scikit-learn ta

#run model-powered predictoor agent
python pdr_backend/predictoor/approach2/main.py
```

## Remote Testnet Usage

To run predictoor as azure container: see [azure-container-deployment.md](azure-container-deployment.md)

To get tokens from testnet: see [testnet-faucet.md](testnet-faucet.md)

## Remote Mainnet Usage

FIXME

