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
- [Dynamic model codebase](READMEs/dynamic-model-codebase.md)
- [Static models in predictoors](READMEs/static-model.md)

## Flows for core team

- **Backend dev** - for `pdr-backend` itself
  - [Main backend-dev README](READMEs/backend-dev.md)
  - [Release process](READMEs/release-process.md)
  - [Run barge locally](READMEs/barge.md)
  - [Run barge remotely on VPS](READMEs/vps.md)
  - [MacOS gotchas](READMEs/macos.md) wrt Docker & ports
- **[Run dfbuyer bot](READMEs/dfbuyer.md)** - runs Predictoor DF rewards
- **[Run publisher](READMEs/publisher.md)** - publish new feeds
- **[Scripts](scripts/)** for performance stats, more

## Repo structure

This repo implements all bots in Predictoor ecosystem.

Each bot has a directory:
- `predictoor` - submits individual predictions
- `trader` - buys aggregated predictions, then trades
- other bots: `trueval` report true values to contract, `dfbuyer` implement Predictoor Data Farming, `publisher` to publish

Other directories:
- `util` - tools for use by any agent
- `models` - classes that wrap Predictoor contracts; for setup (BaseConfig); and for data feeds (Feed)

