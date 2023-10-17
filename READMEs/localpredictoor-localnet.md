<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Run Local Predictoor Bot, Local Network

This README describes:
- Running a *local predictoor* bot (agent)
- On a *local network*, where other bots are local

**Steps:**

1. **Setup & run local network**
    - [Install it](#install-local-network)
    - [Run it](#run-local-network)
2. **Setup & run predictoor bot**
    - [Install it](#install-predictoor-bot)
    - [Set envvars](#set-envvars)
    - [Run it](#run-predictoor-bot): [random](#run-random-predictoor) then [model-based](#run-model-based-predictoor)

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

- It runs [`predictoor_agent1.py::PredictoorAgent1`](../pdr_backend/predictoor/approach1/predictoor_agent1.py) found in `pdr_backend/predictoor/approach1`
- It's configured by envvars and [`predictoor_config1.py::PredictoorConfig1`](../pdr_backend/predictoor/approach1/predictoor_config1.py)
- It predicts according to `PredictoorAgent1:get_prediction()`.

In work console:
```console
# run random predictoor bot
python pdr_backend/predictoor/main.py 1
```

Observe the bots in action:
- In the barge console: trueval bot submitting (mock random) truevals, trader is (mock) trading, etc
- In your work console: predictoor bot is submitting (mock random) predictions

You can query predictoor subgraph for detailed run info. [`subgraph.md`](subgraph.md) has details.


### Run Model Based Predictoor

Since random predictions aren't accurate, let's use AI/ML models. Here's an example flow that loads pre-learned models ("approach2"):

- The bot runs from [`predictoor/approach2/main.py`](../pdr_backend/predictoor/approach2/main.py), using `predict.py` in the same dir.
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

#run model-powered predictoor bot
python pdr_backend/predictoor/main.py 2
```

## Next step

You're now running a local predictoor bot on a local network. Congrats!

The next step is to run a local predictoor bot on a _remote_ network. [Here's the README](./localbot-remotenet.md).

## Other READMEs

- [Parent predictoor README: predictoor.md](./predictoor.md)
- [Root README](../README.md)