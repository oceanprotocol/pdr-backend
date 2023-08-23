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
./start_ocean.sh --predictoor --with-pdr-trueval --with-pdr-trader --with-pdr-publisher --with-pdr-dfbuyer
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
export PRIVATE_KEY="0xef4b441145c1d0f3b4bc6d61d29f5c6e502359481152f869247c7a4244d45209"
```

### Local Usage: Random Predictions

To get started, let's run a predictoor agent with _random_ predictions.

In work console:
```console
# run random predictoor agent
python3 pdr_backend/predictoor/main.py
```

Observe the agents in action:
- in the barge console: trueval agent submitting (mock random) truevals, trader is (mock) trading, etc
- in your work console: predictoor agent is submitting (mock random) predictions

Under the hood, the predictoor agent predicts according to the `predict()` function in [`pdr_backend/predictoor/predict.py`](../pdr_backend/predictoor/predict.py). Its docstring has details.

You can query predictoor subgraph for detailed run info. [`subgraph.md`](subgraph.md) has details.

### Local Usage: Model-based Predictions

Since random predictions aren't accurate, let's use AI/ML models. For illustration, we use models from [`pdr-model-simple`](https://github.com/oceanprotocol/pdr-model-simple) repo. Once you're familiar with this, you'll want to fork it and run your own.

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
python pdr_backend/predictoor/examples/models/main.py
```

## Remote Testnet Usage

FIXME

## Remote Mainnet Usage

FIXME

