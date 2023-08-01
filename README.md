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

## Usage for Frontend Devs

For those developing predictoor.ai or other frontends. Uses barge locally. Backend components don't change.

**[Frontend-dev](READMEs/frontend-dev.md)**

## Usage for Backend Devs, Predictoors, Traders

This flow is for those who want to change one or more backend components
- Ocean S3 backend devs
- Predictoors - focus on changing predictoor component
- Traders - focus on changing trader component

**Follow these steps sequentially:**

**1. Install pdr-backend**
  - [Install](READMEs/install.md)

**2. Run basic debugging setup:** local chain, local agents, one process for all agents
  - [Setup local chain](READMEs/setup-local.md). Run ganache, deploy Ocean, create accounts
  - [Deploy DT3](READMEs/deploy-dt3.md) - to ganache
  - [Run agents-local-oneprocess](READMEs/agents-local-oneprocess.md)
  - Observe, test, customize, etc (details below)

**3. Switch local agents to: each agent gets its own process**
  - (Turn off previous agents)
  - [Run agents-local-manyprocess](READMEs/agents-local-manyprocess.md)
  - Observe, test, customize, etc (details below)

**4. Switch chain to remote testnet**
  - (Turn off previous chain & agents)
  - [Setup remote](READMEs/setup-remote.md) - with *testnet* settings
  - [Deploy DT3](READMEs/deploy-dt3.md) - to remote testnet
  - [Run agents-local-manyprocess](READMEs/agents-local-manyprocess.md)
  - Observe, test, customize, etc (details below)

**5. Switch agents to remote (on Azure)**
  - (Turn off previous agents)
  - [Run agents-remote](READMEs/agents-remote.md) - use existing, or deploy own
  - Observe, test, customize, etc (details below)

**6. Switch chain to remote mainnet - for the real $**
  - (Turn off previous)
  - [Setup remote](READMEs/setup-remote.md) - with *mainnet* settings
  - [Run agents-remote](READMEs/agents-remote.md) - use existing, or deploy own
  - Observe, test, customize, etc (details below)

**How to observe:**

- Relax & watch as predictoor submits random predictions , trueval submits random true_vals for each epoch and trader signals trades.
- You can query [subgraph](http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph/graphql) and see [this populated data PR](https://github.com/oceanprotocol/ocean-subgraph/pull/678) here for entities 

**How to test:**

In console:
```console
#run a single test
pytest pytest pdr_backend/trueval/test/test_trueval.py::test_trueval1

#run all tests in a file
pytest pytest pdr_backend/trueval/test/test_trueval.py

#run all regular tests; see details on pytest markers to select specific suites
pytest
```

**How to customize:**

- Customize `pdr_backend/trueval` to submit real data, not random.
- Customize `pdr_backend/predictoor` to submit real predictions, not random.
- Customize `pdr_backend/trader` to actually trade.

## Release Process

(FIXME)


## 2.x Backend Devs: (OLD) Quickstart


Quickstart
- **[Backend-dev-local](READMEs/backend-dev-local.md)** -- Local components
- **[Backend-dev-remote](READMEs/backend-dev-remote.md)** -- Remote components

Then, observe:
- Relax & watch as pdr-predictoor is submitting random predictions , pdr-trueval submits random true_vals for each epoch and pdr-trader signals trades.
- You can query [subgraph](http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph/graphql) and see [this populated data PR](https://github.com/oceanprotocol/ocean-subgraph/pull/678) here for entities 
