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

A "ppss" yaml file, like [`ppss.yaml`](ppss.yaml), holds parameters for all bots and simulation flows.

- We follow the idiom "pp" = problem setup (what to solve), "ss" = solution strategy (how to solve).
- `PRIVATE_KEY` is an exception; it's set as an envvar.

When you run a bot from the CLI, you specify your PPSS YAML file.

pdr has basic stdout logging, but supports customisations.
To customise logging, copy and edit the existing `logging.yaml`:

```console
cp logging.yaml my_logging.yaml
```

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
  pdr predictoor YAML_FILE NETWORK
  pdr trader APPROACH YAML_FILE NETWORK
...
```

## Atomic READMEs

- [Get tokens](READMEs/get-tokens.md): [testnet faucet](READMEs/testnet-faucet.md), [mainnet ROSE](READMEs/get-rose-on-sapphire.md) & [OCEAN](READMEs/get-ocean-on-sapphire.md)
- [Claim payout for predictoor bot](READMEs/payout.md)
- [Predictoor subgraph](READMEs/subgraph.md). [Subgraph filters](READMEs/filters.md)
- [Run barge locally](READMEs/barge.md)

## Flows for core team

- Backend-dev - for `pdr-backend` itself
  - [Local dev flow](READMEs/dev.md)
  - [VPS dev flow](READMEs/vps.md)
  - [Release process](READMEs/release-process.md)
  - [Clean code guidelines](READMEs/clean-code.md)
- [Run dfbuyer bot](READMEs/dfbuyer.md) - runs Predictoor DF rewards
- [Run publisher](READMEs/publisher.md) - publish new feeds
- [Run trueval](READMEs/trueval.md) - run trueval bot

## Repo structure

This repo implements all bots in Predictoor ecosystem. Here are each of the sub-directories in the repo.

Main bots & user tools:

- `predictoor` - submit individual predictions
- `trader` - buy aggregated predictions, then trade
- `sim` - experiments / simulation flow
- `payout` - OCEAN & ROSE payout

OPF-run bots & higher-level tools:

- `trueval` - report true values to contract
- `dfbuyer` - buy feeds on behalf of Predictoor DF
- `publisher` - publish pdr data feeds
- `lake` - data lake and analytics tools
- `deployer` - deployer tool
- `accuracy` - calculates % correct, for display in predictoor.ai webapp

Mid-level building blocks:

- `cli` - implementation of CLI
- `ppss` - implements settings
- `ohlcv` - financial data pipeline
- `subgraph` - blockchain queries, complements lake
- `aimodel` - AI/ML modeling engine
- `accuracy` - to report % correct in webapp
- `pred_submitter` - for predictoor bots to submit >>1 predictions in 1 tx

Lower-level utilities:

- `contract` - classes to wrap blockchain contracts; some simple data structures
- `util` - function-based tools
