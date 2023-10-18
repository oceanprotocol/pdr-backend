<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Run Local Trader Bot, Local Network

This README describes:
- Running a *local trader* bot (agent)
- On a *local* network, where other bots are local
- It doesn't use Docker containers

**Steps:**

1. **Setup & run local network (Barge)**
    - [Install it](#install-local-network)
    - [Run it](#run-local-network)
2. **Setup & run trader bot**
    - [Install it](#install-trader-bot)
    - [Set envvars](#set-envvars)
    - [Run it](#run-trader-bot)


## Install Local Network

"Barge" is a Docker container that runs a local Ganache network and off-the-shelf agents.

[Install barge](barge.md#install-barge).

## Run Local Network

In barge console:
```console
# set ganache block time to 5 seconds, try increasing this value if barge is lagging
export GANACHE_BLOCKTIME=5

#run barge with all bots (agents) except trader
./start_ocean.sh --no-aquarius --no-elasticsearch --no-provider --no-dashboard --predictoor --with-thegraph --with-pdr-trueval --with-pdr-predictoor --with-pdr-publisher --with-pdr-dfbuyer
```

## Install Trader Bot

The trader bot runs code that lives in `pdr-backend` repo.

[Install pdr-backend](install.md).

## Set Envvars

Open a new "work" console and:
```
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


## Run Trader Bot

Here, we run a simple trading bot. Its default strategy is simplistic; you need to customize it. 

- It runs [`trader_agent.py::TraderAgent`](../pdr_backend/trader/trader_agent.py) found in `pdr_backend/trader/`
- It's configured by envvars and [`trader_config.py::TraderConfig`](../pdr_backend/trader/trader_config.py)

In work console:
```console
# run trader bot (agent)
python pdr_backend/trader/main.py
```

You can query predictoor subgraph for detailed run info. See [subgraph.md](subgraph.md) for details.

## Next step

You're now running a local trader bot on a local network. Congrats!

The next step is to run a local trader bot on a _remote_ network. [Here's the README](./localbot-remotenet.md).

## Other READMEs

- [Parent trader README: trader.md](./trader.md)
- [Root README](../README.md)
