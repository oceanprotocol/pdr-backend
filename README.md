<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# pdr-backend

## Run bots (agents)

- **[Run predictoor bot](READMEs/predictoor.md)** - make predictions, make $
- **[Run trader bot](READMEs/trader.md)** - consume predictions, trade, make $

(If you're a predictoor or trader, you can safely ignore the rest of this README.)

## Atomic READMEs

- [Get tokens](READMEs/get-tokens.md): [testnet faucet](READMEs/testnet-faucet.md), [mainnet ROSE](READMEs/get-rose-on-sapphire.md) & [OCEAN](READMEs/get-ocean-on-sapphire.md)
- [Envvars](READMEs/envvars.md)
- [Predictoor subgraph](READMEs/subgraph.md). [Subgraph filters](READMEs/filters.md)

Optional, less useful:
- [Static models in predictoors](READMEs/static-model.md)
- [Install & run local network (Barge)](READMEs/barge.md)
- [MacOS gotchas](READMEs/macos.md) wrt Docker & ports

## Flows for core team

- **[Backend-dev README](READMEs/backend-dev.md)** - for `pdr-backend` itself
  - [Release process](READMEs/release-process.md)
- **[Run dfbuyer bot](READMEs/dfbuyer.md)** - runs Predictoor DF rewards
- **[Run publisher](READMEs/publisher.md)** - publish new feeds
- [Frontend-dev README](READMEs/frontend-dev.md) - for predictoor.ai

## Repo structure

This repo implements all bots in Predictoor ecosystem.

Each bot has a directory:
- `predictoor` - submits individual predictions
- `trader` - buys aggregated predictions, then trades
- other bots: `trueval` report true values to contract, `dfbuyer` implement Predictoor Data Farming, `publisher` to publish

Other directories:
- `util` - tools for use by any agent
- `models` - classes that wrap Predictoor contracts; for setup (BaseConfig); and for data feeds (Feed)

