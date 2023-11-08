<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Usage for Backend Devs

This is for core devs to improve pdr-backend repo itself.

## Install pdr-backend

Follow directions to install pdr-backend in [predictoor.md](predictoor.md)

## Local Network

First, [install barge](barge.md#install-barge).

Then, run barge. In barge console:
```console
# Run barge with just predictoor contracts, queryable, but no agents
./start_ocean.sh --no-provider --no-dashboard --predictoor --with-thegraph
```

Open a new "work" console and:
```console
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

([envvars.md](envvars.md) has details.)

### Local Usage: Testing & linting

In work console, run tests:
```console
#(ensure envvars set as above)

#run a single test
pytest pdr_backend/util/test/test_constants.py::test_constants1

#run all tests in a file
pytest pdr_backend/util/test/test_constants.py

#run all regular tests; see details on pytest markers to select specific suites
pytest
```

In work console, run linting checks:
```console
#run static type-checking. By default, uses config mypy.ini. Note: pytest does dynamic type-checking.
mypy ./

#run linting on code style
pylint pdr_backend/*

#auto-fix some pylint complaints
black ./
```

### Local Usage: Run a custom agent

Let's say you want to change the trader agent, and use off-the-shelf agents for everything else. Here's how.

In barge console:
```console
# (Hit ctrl-c to stop existing barge)

# Run all agents except trader
./start_ocean.sh --predictoor --with-thegraph --with-pdr-trueval --with-pdr-predictoor --with-pdr-publisher --with-pdr-dfbuyer
```

In work console:
```console
#(ensure envvars set as above)

# run trader agent
python pdr_backend/trader/main.py
```

(You can track at finer resolution by writing more logs to the [code](../pdr_backend/predictoor/approach3/predictoor_agent3.py), or [querying Predictoor subgraph](subgraph.md).)

## Remote Usage

Combine local setup above with remote setup envvars like in [predictoor.md](predictoor.md).
