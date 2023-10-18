<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# pdr-backend

## Run bots (agents)

- **[Run predictoor bot](READMEs/predictoor.md)** - make predictions, make $
- **[Run trader bot](READMEs/trader.md)** - consume predictions, trade, make $

## OPF bots

- **[Run dfbuyer bot](READMEs/dfbuyer.md)** - for Predictoor DF rewards

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

The `predictoor` and `trader` agents are meant to be customized by predictoor and trader stakeholders, respectively.

Other directories:
- `util` - tools for use by any agent
- `models` - classes that wrap Predictoor contracts; for setup (BaseConfig); and for data feeds (Feed)
- `publisher` - used for publishing

## Atomic READMEs

The following READMEs are used as building blocks within different flows.

Installation & setup:
- [Install pdr-backend](READMEs/install.md)
- [Install & use Barge](READMEs/barge.md)
- [Envvars](READMEs/envvars.md)
- [MacOS gotchas](READMEs/macos.md)

Usage:
- [Get tokens](READMEs/get-tokens.md): [testnet faucet](READMEs/testnet-faucet.md), [mainnet ROSE](READMEs/get-rose-on-sapphire.md) & [OCEAN](READMEs/get-ocean-on-sapphire.md)
- [Predictoor subgraph](READMEs/subgraph.md). [Subgraph filters](READMEs/filters.md)
- [Models: dynamic](READMEs/dynamic-model.md), [static](READMEs/static-model.md)
- [Claim payout](READMEs/payout.md)

Development:
- [Release process](READMEs/release-process.md)
