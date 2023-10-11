<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Run Local Predictoor Bot, Local Network

This README describes:
- Running a *local predictoor* bot (agent)
- On a *local network*, where other bots are local
- It doesn't use Docker containers

**Steps:**

1. **Setup & run local network**
    - [Install it](#install-local-network)
    - [Run it](#run-local-network)
2. **Setup predictoor bot**
    - [Install it](#install-predictoor-bot)
    - [Set envvars](#set-envvars)
3. **[Run predictoor bot](#run-predictoor-bot)**
    - [Random](#run-random-predictoor)
    - [Static model](#run-static-model-predictoor)
    - [Dynamic model](#run-dynamic-model-predictoor)

## Install Local Network

"Barge" is a Docker container that runs a local Ganache network and off-the-shelf agents.

[Install barge](barge.md#install-barge).

## Run Local Network

In barge console:
```console
# set ganache block time to 5 seconds, try increasing this value if barge is lagging
export GANACHE_BLOCKTIME=5

#run barge with all bots except predictoor
./start_ocean.sh --no-aquarius --no-elasticsearch --no-provider --no-dashboard --predictoor --with-thegraph --with-pdr-trueval --with-pdr-trader --with-pdr-publisher --with-pdr-dfbuyer
```

## Install Predictoor Bot

The predictoor bot runs code that lives in `pdr-backend` repo.

[Install pdr-backend](install.md).

## Set Envvars

Open a new "work" console and:
```console
# Setup virtualenv
cd pdr-backend
source venv/bin/activate

# Set envvars
export ADDRESS_FILE="${HOME}/.ocean/ocean-contracts/artifacts/address.json"
export RPC_URL=http://127.0.0.1:8545
export SUBGRAPH_URL="http://localhost:9000/subgraphs/name/oceanprotocol/ocean-subgraph"
#OR: export SUBGRAPH_URL="http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph"
export PRIVATE_KEY="0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58"
```

There are other envvars that you might want to set, such as the owner addresses. The [envvars README](./envvars.md) has more info.

## Run Predictoor Bot

### Run Random Predictoor

Here, we run a bot that makes random predictions.

In work console:
```console
# run random predictoor bot
python pdr_backend/predictoor/main.py 1
```

Observe the bots in action:
- In the barge console: trueval bot submitting (mock random) truevals, trader is (mock) trading, etc
- In your work console: predictoor bot is submitting (mock random) predictions
- Query predictoor subgraph for detailed run info. [`subgraph.md`](subgraph.md) has details.

Code structure:
- It runs [`predictoor_agent1.py::PredictoorAgent1`](../pdr_backend/predictoor/approach1/predictoor_agent1.py) found in `pdr_backend/predictoor/approach1`
- It's configured by envvars and [`predictoor_config1.py::PredictoorConfig1`](../pdr_backend/predictoor/approach1/predictoor_config1.py)
- It predicts according to `PredictoorAgent1:get_prediction()`.

### Run Static Model Predictoor

Since random predictions aren't accurate, let's use AI/ML models.
- Here in "approach2", we load pre-learned models (static)
- And in "approach3" further below, we learn models on-the-fly (dynamic)

Code structure:
- The bot runs from [`predictoor/approach2/main.py`](../pdr_backend/predictoor/approach2/main.py), using `predict.py` in the same dir.
- Which imports a model stored in [`pdr-model-simple`](https://github.com/oceanprotocol/pdr-model-simple) repo

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

#run model-powered predictoor bot
python pdr_backend/predictoor/main.py 2
```

Once you're familiar with this, you can fork it and run your own.

### Run Dynamic Model Predictoor

Here, we build models on-the-fly, ie dynamic models. It's "approach3".

Whereas approach2 has model development in a different repo, approach3 has it inside this repo. Accordingly, this flow has two top-level steps:
1. Develop & backtest models
2. Run bot in Predictoor context

Let's go through each in turn.

**Approach3 - Step 1: Develop & backtest models**

Here, we develop & backtest the model. The setup is optimized for rapid iterations, by being independent of Barge and Predictoor bots.

In work console:
```console
#this dir will hold data fetched from exchanges
mkdir csvs

#run approach3 unit tests
pytest pdr_backend/predictoor/approach3

#run approach3 backtest.
# (Edit the parameters in runtrade.py as desired)
python pdr_backend/predictoor/approach3/runtrade.py
```

`runtrade.py` will grab data from exchanges, then simulate one epoch at a time (including building a model, predicting, and trading). When done, it plots accumulated returns vs. time. Besides logging to stdout, it also logs to out*.txt in pwd.

**Approach3 - Step 2: Run bot in Predictoor context**

Once you're satisfied with your backtests, you're ready to run the approach3 bot in a Predictoor context.

First, get Barge & other bots going via "Run local network" instructions above.

Then, in work console:
```console
# run approach3 predictoor bot
python pdr_backend/predictoor/main.py 3
```

Observe all bots in action:
- In the barge console: trueval bot submitting (mock random) truevals, trader is (mock) trading, etc
- In your work console: predictoor bot is submitting (mock random) predictions
- Query predictoor subgraph for detailed run info. [`subgraph.md`](subgraph.md) has details.

Code structure:
- It runs [`predictoor_agent3.py::PredictoorAgent3`](../pdr_backend/predictoor/approach3/predictoor_agent3.py) found in `pdr_backend/predictoor/approach3`
- It's configured by envvars and [`predictoor_config3.py::PredictoorConfig3`](../pdr_backend/predictoor/approach3/predictoor_config3.py)
- It predicts according to `PredictoorAgent3:get_prediction()`.

Once you're familiar with this, you can fork it and run your own.