<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# pdr-backend

## Run bots (agents)

- **[Run predictoor bot](READMEs/predictoor.md)** - make predictions, make $
- **[Run trader bot](READMEs/trader.md)** - consume predictions, trade, make $


(If you're a predictoor or trader, you can safely ignore the rest of this README.)

## Settings: PPSS

A single "ppss" yaml file holds parameters for all bots and simulation flows.
- See [`sample_ppss.yaml`](sample_ppss.yaml) for an example.
- We follow the idiom "pp" = problem setup (what to solve), "ss" = solution strategy (how to solve).
- `PRIVATE_KEY` is an exception; it's set as an envvar.

When you run a bot from the CLI, you specify your PPSS YAML file.

## CLI

(First, [install pdr-backend](READMEs/predictoor.md#install-pdr-backend-repo) first.)

To see CLI options, in console:
```console
pdr
```

This will output something like:
```text
Usage: pdr sim|predictoor|trader|..

Main tools:
  pdr sim YAML_FILE
  pdr predictoor APPROACH NETWORK YAML_FILE
  pdr trader APPROACH NETWORK YAML_FILE
...
```


## Atomic READMEs

- [Get tokens](READMEs/get-tokens.md): [testnet faucet](READMEs/testnet-faucet.md), [mainnet ROSE](READMEs/get-rose-on-sapphire.md) & [OCEAN](READMEs/get-ocean-on-sapphire.md)
- [Predictoor subgraph](READMEs/subgraph.md). [Subgraph filters](READMEs/filters.md)
- [Run barge locally](READMEs/barge.md)
- [Static models in predictoors](READMEs/static-model.md)

## Flows for core team

- **Backend dev** - for `pdr-backend` itself
  - [Main backend-dev](READMEs/backend-dev.md)
  - [VPS backend-dev](READMEs/vps.md)
  - [Release process](READMEs/release-process.md)
- **[Run dfbuyer bot](READMEs/dfbuyer.md)** - runs Predictoor DF rewards
- **[Run publisher](READMEs/publisher.md)** - publish new feeds
- **[Scripts](scripts/)** for performance stats, more

## Repo structure

This repo implements all bots in Predictoor ecosystem.

Each bot has a directory:
- `predictoor` - submits individual predictions
- `trader` - buys aggregated predictions, then trades
- `trueval` - report true values to contract
- `dfbuyer` - implement Predictoor DF
- `publisher` - publish pdr data feeds

Other directories:
- `sim` - simulation flow
- `ppss` - all settings, both problem setup (pp) and solution strategy (ss)
- `util` - function-based tools
- `models` - classes that wrap Predictoor contracts, and class-based data structures
- `data_eng` - data engineering & modeling
- `accuracy` - calculates % correct, for display in predictoor.ai webapp

