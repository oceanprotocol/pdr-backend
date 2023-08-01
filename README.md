<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# pdr-backend

## 0. Overview

This is the repo for Predictoor backend.

- This repo merges prior repos: pdr-utils + pdr-trueval + pdr-predictoor + pdr-trader + pdr-dfbuyer.
  - Each has its own sub-directory
  - Each has its own unit tests
- Plus system-level tests
- Plus system-level READMEs

(Once it's working, we no longer need any of the above pdr-* repos)

## 1. Usage/Dev: Frontend Devs

### 1.1 Frontend Devs: Quickstart

For those developing predictoor.ai or other frontends. Uses barge locally. Backend components don't change.

**[Frontend-dev](READMEs/frontend-dev.md)**

# 2. Usage/Dev: Backend Devs, Predictoors, Traders

### 2.1 Backend Devs: Quickstart

For those who want to change backend components (predictoor, trader, ..)

Follow these steps in sequence.

 1. **[Install pdr-backend](READMEs/install.md)**
 2. **Setup.** Outcome is a running chain + Ocean contracts + accounts
    - **[Local](READMEs/setup-local.md)**, *or* 
    - **[Remote](READMEs/setup-remote.md)** 
 3. **[Deploy DT3](READMEs/deploy-dt3.md)**
 3. **[Walk through main flow](READMEs/main-flow.md)**: run agents (trueval, predictoor, trader)


### 2.2 Backend Devs: Testing

In console:
```console
#run a single test
pytest ocean_lib/models/test/test_data_nft_factory.py::test_start_multiple_order

#run all tests in a file
pytest ocean_lib/models/test/test_data_nft_factory.py

#run all regular tests; see details on pytest markers to select specific suites
pytest
```


### 2.2 Backend Devs: Customize

Ways to customize
- Customize [pdr-trueval](https://github.com/oceanprotocol/pdr-trueval) to submit real data, not random.
- Customize [pdr-predictoor](https://github.com/oceanprotocol/pdr-predictoor) to submit real predictions, not random.
- Customize [pdr-trader](https://github.com/oceanprotocol/pdr-trader) to actually trade.

### 2.4 Backend Devs: Release Process

(FIXME)


### 2.x Backend Devs: (OLD) Quickstart


Quickstart
- **[Backend-dev-local](READMEs/backend-dev-local.md)** -- Local components
- **[Backend-dev-remote](READMEs/backend-dev-remote.md)** -- Remote components

Then, observe:
- Relax & watch as pdr-predictoor is submiting random predictions , pdr-trueval submits random true_vals for each epoch and pdr-trader signals trades.
- You can query [subgraph](http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph/graphql) and see [this populated data PR](https://github.com/oceanprotocol/ocean-subgraph/pull/678) here for entities 
