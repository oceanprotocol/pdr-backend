<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Run a DFBuyer Bot

This README describes how to run a dfbuyer bot.

## Install pdr-backend

Follow directions in [predictoor.md](predictoor.md)

## Local Network

First, [install barge](barge.md#install-barge).

Then, run barge. In barge console:
```console
#run barge with all bots (agents) except dfbuyer
./start_ocean.sh --no-provider --no-dashboard --predictoor --with-thegraph --with-pdr-trueval --with-pdr-predictoor --with-pdr-publisher --with-pdr-trader
```

Open a new console and:
```
# Setup virtualenv
cd pdr-backend
source venv/bin/activate

# Set envvars
export PRIVATE_KEY="0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58"
export ADDRESS_FILE="${HOME}/.ocean/ocean-contracts/artifacts/address.json"

export RPC_URL=http://127.0.0.1:8545
export SUBGRAPH_URL="http://localhost:9000/subgraphs/name/oceanprotocol/ocean-subgraph"
#OR: export SUBGRAPH_URL="http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph"
```

Then, run dfbuyer bot. In console:
```console
python pdr_backend/dfbuyer/main.py
```

There are other environment variables that you might want to set, such as the **weekly spending limit**. To get more information about them check out the [environment variables documentation](./envvars.md).

The bot will consume "WEEKLY_SPENDING_LIMIT" worth of assets each week. This amount is distributed equally among all DF eligible assets.

![flow](https://user-images.githubusercontent.com/25263018/269256707-566b9f5d-7e97-4549-b483-2a6700826769.png)

## Remote Usage

Combine local setup above with remote setup envvars like in [predictoor.md](predictoor.md).

