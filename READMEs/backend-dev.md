<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Usage for Backend Devs

## 1. Introduction

This is for backend devs working on `pdr-backend` itself

## 2. Install pdr-backend

Follow instructions in [install.md](install.md).

## 3. Install barge

Follow instructions in [barge.md "install"](barge.md#install-barge).

## 4. Run barge

We'll use barge to run just these components:
- local chain (ganache)
- predictoor-related smart contracts deployed to chain

(We'll run predictoor agents directly as we develop against them.)

In barge console:
```console
./start_ocean.sh --predictoor
```

## 5. Set up environment

Start a new console and:
```
# Setup env
cd pdr-backend
source venv/bin/activate

# Set envvars
export ADDRESS_FILE="${HOME}/.ocean/ocean-contracts/artifacts/address.json"
export RPC_URL=http://127.0.0.1:8545
export SUBGRAPH_URL="http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph"
export PRIVATE_KEY="0xef4b441145c1d0f3b4bc6d61d29f5c6e502359481152f869247c7a4244d45209"
```

## 6. Usage


## 6.1 Usage: Testing

In a console, first ensure environment is set up (see previous section).

Then in the console:
```console
#run a single test
pytest pdr_backend/utils/test/test_constants.py::test_constants1

#run all tests in a file
pytest pdr_backend/utils/test/test_constants.py

#run all regular tests; see details on pytest markers to select specific suites
pytest
```

### 6.2 Usage: Run a custom agent

Let's say you want to change the trader agent, and use off-the-shelf agents for everything else. Here's how.

In barge console:
```console
# (Hit ctrl-c to stop existing barge)

# Run all agents except trader
./start_ocean.sh --predictoor --with-pdr-trueval --with-pdr-predictoor --with-pdr-publisher --with-pdr-dfbuyer
```

Open a new console and:
```console
# Set envvars
# (copy and paste the envvar-setting code above)

# run trader agent
python3 pdr_backend/trader/main.py
```

### 6.3 Usage: Places to customize

Here are possible places to customize:
- [`pdr_backend/trueval/trueval.py`](pdr_backend/trueval/trueval.py) - to submit real data, not random
- [`pdr_backend/predictoor/predict.py`](pdr_backend/predictoor/predict.py) - to submit real predictions, not random
- [`pdr_backend/trader/trade.py`](pdr_backend/trader/trade.py) - to actually trade


### 6.4 Usage: How to observe

Relax & watch as predictoor submits random predictions , trueval submits random true_vals for each epoch and trader signals trades.

You can query [subgraph](http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph/graphql) and see [this populated data PR](https://github.com/oceanprotocol/ocean-subgraph/pull/678) here for entities 


### 6.5 Usage: How to filter

Here are additional envvars used to filter:

- PAIR_FILTER = if we do want to act upon only same pair, like  "BTC/USDT,ETH/USDT"
- TIMEFRAME_FILTER = if we do want to act upon only same timeframes, like  "5m,15m"
- SOURCE_FILTER = if we do want to act upon only same sources, like  "binance,kraken"
- OWNER_ADDRS = if we do want to act upon only same publishers, like  "0x123,0x124"


### 7. Release Process

Follow instructions in [release-process.md](release-process.md).


### Appendix: Create & run agents in a single process

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




