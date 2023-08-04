<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# pdr-backend

## 1. Overview

This is the repo for Predictoor backend.

- This repo merges prior repos: pdr-utils + pdr-trueval + pdr-predictoor + pdr-trader + pdr-dfbuyer.
  - Each has its own sub-directory
  - Each has its own unit tests
- Plus system-level tests
- Plus system-level READMEs

(Once it's working, we no longer need any of the above pdr-* repos)

## 2. Install

- [Install pdr-backend](READMEs/install.md)

## 3. Usage for Frontend

This is for frontend devs who are developing predictoor.ai etc. Uses barge locally. Backend components don't change.

First, [set up barge](READMEs/setup-barge.md).

Then, run barge with all components: `./start_ocean.sh --predictoor --with-pdr-trueval --with-pdr-trader --with-pdr-predictoor --with-pdr-publisher --with-pdr-dfbuyer`

Then, run frontend components that talk to chain & agents in barge, via http api.

## 4. Usage for Backend Devs, Predictoors, Traders

### 4.1 Usage for Backend: Overview

This flow is for those who want to change one or more backend components
- Ocean S3 backend devs
- Predictoors - focus on changing predictoor component
- Traders - focus on changing trader component

### 4.2 Usage for Backend: Local variants

First, [set up barge](READMEs/setup-barge.md).

Then, use any configuration below.

**Local chain, local agents all in one synchronous process**
  - Run barge with no predictoor agents: `./start_ocean.sh --predictoor`
  - [Run agents-local-oneprocess](READMEs/agents-local-oneprocess.md)
  - Observe, test, filter, customize, etc (details below)

**Local chain, iterate on predictoor agent changes, other agents in barge**
  - Run barge with all agents except predictoor agent:  `./start_ocean.sh --predictoor --with-pdr-trueval --with-pdr-trader --with-pdr-publisher --with-pdr-dfbuyer`
  - Run a predictoor agent from pdr-util as follows. Start new console and:
```console
# Setup env
cd pdr-backend
source venv/bin/activate

# Set envvars
export ADDRESS_FILE="${HOME}/.ocean/ocean-contracts/artifacts/address.json"
export RPC_URL=http://127.0.0.1:8545
export SUBGRAPH_URL="http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph"
export PRIVATE_KEY="0xef4b441145c1d0f3b4bc6d61d29f5c6e502359481152f869247c7a4244d45209"

# Run
python3 pdr_backend/predictoor/main.py
```

**Local chain, iterate changes to agent XX1, with other agents in barge**
  - Where XX1 can be trader, trueval, dfbuyer, etc
  - Do like "predictoor" above, except predictoor --> XX1


**Local chain, iterate changes to agent {XX1, XX2, ..}, with other agents in barge**
  - Where XX1, XX2, .. can be trader, trueval, dfbuyer, etc
  - Do like "predictoor" above, except one new console for each of XX1, XX2, etc


### 4.3 Usage for Backend: Remote, for Predictoors

(WIP, don't worry about this for now!)

**Remote testnet, local predictoor, other agents run remotely by others**
  - [Setup remote](READMEs/setup-remote.md) - with *testnet* settings
  - Run predictoor with settings like above, except set RPC to remote
  - Observe, test, filter, customize, etc (details below)

**Remote testnet, remote predictoor, other agents run remotely by others**
  - [Setup remote](READMEs/setup-remote.md) - with *testnet* settings
  - Deploy predictoor to Azure. Details in [Run agents-remote](READMEs/agents-remote.md)

*Remote mainnet, remote predictoor*
  - [Setup remote](READMEs/setup-remote.md) - with *mainnet* settings
  - [Run agents-remote](READMEs/agents-remote.md) - use existing, or deploy own

(For non-predictoors, it's similar. We'll flesh this out as we go.)

### 4.4 Usage for Backend: How to observe

- Relax & watch as predictoor submits random predictions , trueval submits random true_vals for each epoch and trader signals trades.
- You can query [subgraph](http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph/graphql) and see [this populated data PR](https://github.com/oceanprotocol/ocean-subgraph/pull/678) here for entities 

### 4.5 Usage for Backend: How to test

In console:
```console
#run a single test
pytest pytest pdr_backend/trueval/test/test_trueval.py::test_trueval1

#run all tests in a file
pytest pytest pdr_backend/trueval/test/test_trueval.py

#run all regular tests; see details on pytest markers to select specific suites
pytest
```

### 4.6 Usage for Backend: How to filter

Here are additional envvars used to filter:

- PAIR_FILTER = if we do want to act upon only same pair, like  "BTC/USDT,ETH/USDT"
- TIMEFRAME_FILTER = if we do want to act upon only same timeframes, like  "5m,15m"
- SOURCE_FILTER = if we do want to act upon only same sources, like  "binance,kraken"
- OWNER_ADDRS = if we do want to act upon only same publishers, like  "0x123,0x124"

### 4.7 Usage for Backend: How to customize

Possible places to customize:
- [`pdr_backend/trueval/trueval.py`](pdr_backend/trueval/trueval.py) - to submit real data, not random
- [`pdr_backend/predictoor/predict.py`](pdr_backend/predictoor/predict.py) - to submit real predictions, not random
- [`pdr_backend/trader/trade.py`](pdr_backend/trader/trade.py) - to actually trade


## 5. Release Process

### Version Number

In the pdr-backend repository, the version and tag name convention follows the format "vx.x.x":
- The version number consists of three parts separated by dots, The first part represents the major version, the second part represents the minor version, and the third part represents the patch version.
- When a new release is created, the version number should be incremented according to the significance of the changes made in the release.

### Create a New Release

To create a new release for pdr-backend, follow these steps:

1. Visit the [Github Releases](https://github.com/oceanprotocol/pdr-backend/releases) page.
2. Click on "Draft a new release."
3. Choose an appropriate version tag (e.g., v1.0.0) and provide a release title.
4. Add release notes and any relevant information about the new release.
5. Once everything is ready, click "Publish release."

The CI/CD will automatically build and publish a new Docker image with the release tag, making it available for installation and use.

## Appendix: OLD backend quickstart

(from pdr-trueval)

**[Here](READMEs/backend-dev-local.md)** 
