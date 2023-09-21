<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# pdr-backend

## Run bots

- **[Run predictoor bot](READMEs/predictoor.md)** - make predictions, make $
- **[Run trader bot](READMEs/trader.md)** - consume predictions, trade, make $

# OPF bots

- **[Run dfbuyer bot](READMEs/dfbuyer.md)** - distribution of Predictoor DF rewards

## Develop predictoor


- [Frontend-dev README](READMEs/frontend-dev.md) - for work on predictoor.ai
- [Backend-dev README](READMEs/backend-dev.md) - for work on pdr-backend
- [Publisher README](READMEs/publisher.md) - for publishing new feeds


## About

The `pdr-backend` repo implements all of the bots (agents) of the Predictoor ecosystem.

Each agent has a directory:
- `predictoor` - bot (agent) that submits individual predictions
- `trader` - bot (agent) that buys aggregated predictions, then trades
- `trueval` - agent that reports true values to contract
- `dfbuyer` - agent that buys aggregate predictions on behalf of Data Farming

Other directories:
- `util` - tools for use by any agent
- `models` - classes that wrap Predictoor contracts; for setup (BaseConfig); and for data feeds (Feed)
- `publisher` - used for publishing

The `predictoor` and `trader` agents are meant to be customized by predictoor and trader stakeholders, respectively.

## Atomic READMEs

The following READMEs are used as building blocks within different flows.
- [Install pdr-backend](READMEs/install.md)
- [Install & use Barge](READMEs/install-barge.md)
- [Using Predictoor subgraph](READMEs/subgraph.md)
- [Getting testnet tokens](READMEs/testnet-faucet.md) - faucets for fake ROSE & OCEAN
- [Azure container deployment](READMEs/azure-container-deployment.md)
- [Release process](READMEs/release-process.md)
- [Environment variables](READMEs/envvars.md)
