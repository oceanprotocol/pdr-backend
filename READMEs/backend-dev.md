<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Usage for Backend Devs

This is for backend devs working on `pdr-backend` itself.

## Contents

- [Install](#install)
- [Local Usage](#local-usage)
- [Remote Testnet Usage](#remote-testnet-usage)
- [Remote Mainnet Usage](#remote-mainnet-usage)
- [Release Process](#release-process)

## Install

First, [install pdr-backend](install.md).

Then, [install barge](barge.md#install-barge).

## Local Usage

First, open a new "work" console and:
```console
# Setup virtualenv
cd pdr-backend
source venv/bin/activate

# Set envvars
export ADDRESS_FILE="${HOME}/.ocean/ocean-contracts/artifacts/address.json"
export RPC_URL=http://127.0.0.1:8545
export SUBGRAPH_URL="http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph"
export PRIVATE_KEY="0xef4b441145c1d0f3b4bc6d61d29f5c6e502359481152f869247c7a4244d45209"
```

Each subsection below gives different local usage options.

### Local Usage: Testing & linting

In barge console:
```console
# Run barge with just predictoor contracts, but no agents
./start_ocean.sh --predictoor
```

In work console, run tests:
```console
#(ensure envvars set as above)

#run a single test
pytest pdr_backend/utils/test/test_constants.py::test_constants1

#run all tests in a file
pytest pdr_backend/utils/test/test_constants.py

#run all regular tests; see details on pytest markers to select specific suites
pytest
```

In work console, run linting checks:
```console
#run static type-checking. By default, uses config mypy.ini. Note: pytest does dynamic type-checking.
mypy ./

#run linting on code style
pylint *

#auto-fix some pylint complaints
black ./
```

### Local Usage: Run a custom agent

Let's say you want to change the trader agent, and use off-the-shelf agents for everything else. Here's how.

In barge console:
```console
# (Hit ctrl-c to stop existing barge)

# Run all agents except trader
./start_ocean.sh --predictoor --with-pdr-trueval --with-pdr-predictoor --with-pdr-publisher --with-pdr-dfbuyer
```

In work console:
```console
#(ensure envvars set as above)

# run trader agent
python3 pdr_backend/trader/main.py
```

Relax & watch as the predictoor agent submits random predictions, trueval submits random truevals for each epoch and trader signals trades.

You can query predictoor subgraph for detailed run info. See [subgraph.md](subgraph.md) for details.

## Remote Testnet Usage

FIXME

## Remote Mainnet Usage

FIXME

## Release Process

Follow instructions in [release-process.md](release-process.md).

## Appendix: Create & run agents in a single process

(If you're feeling extra bold)

In Python console:
```python
import time
from pdr_backend.trueval.trueval import process_block as trueval_process_block
# FIXME: add similar for predictoor, trader, etc

print("Starting main loop...")
trueval_lastblock = 0
while True:
    # trueval agent
    trueval_block = web3_config.w3.eth.block_number
    if block > lastblock:
        trueval_lastblock = trueval_block
        trueval_process_block(web3_config.w3.eth.get_block(trueval_block, full_transactions=False))
    else:
        time.sleep(1)
    # FIXME: add similar for predictoor, trader, etc
```




