<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# pdr-backend: Predictoor Backend

## Quickstart, per Stakeholder

Main
- If you are a **predictoor**, do [Predictoor README](READMEs/predictoor.md)
- If you are a **trader**, do [Trader README](READMEs/trader.md)

Developers
- If you are a **frontend dev** working on predictoor.ai: do [Frontend-Dev README](READMEs/frontend-dev.md)
- If you are a **backend dev** working on `pdr-backend` itself: do [Backend-Dev README](READMEs/backend-dev.md)
- If you are a **publisher**: do [Publisher README](READMEs/publisher.md)

## About

The `pdr-backend` repo implements all of the agents of the Predictoor ecosystem.

Each agent has a directory:
- `predictoor` - agent that submits individual predictions
- `trader` - agent that buys aggregated predictions, then trades
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
- [Getting testnet tokens](READMEs/testnet-faucet.md) - fake ROSE & OCEAN
- [Azure container deployment](READMEs/azure-container-deployment.md)
- [Release process](READMEs/release-process.md)
