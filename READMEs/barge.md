<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Barge

Barge is a Docker container to run a local Ganache network having Predictoor contracts and (optionally) local bots. This README describes how to install Barge, and provides reference on running it with various agents.

⚠️ If you're on MacOS or Windows, we recommend using a remotely-run Barge. See [vps flow](vps.md).

## Contents

Main:
- [Install Barge](#install-barge)

Reference: how to run barge with...
- [No agents](#barge-basic) - just ganache network & Predictoor contracts
- [One agent](#barge-one-agent) - eg trueval bot
- [All agents](#barge-all-agents) - predictoor, trader, trueval, dfbuyer bots

Finally:
- [Change Barge Itself](#change-barge-itself)


## Install Barge

**First, ensure pre-requisites:** [Docker](https://docs.docker.com/engine/install/), [Docker Compose](https://docs.docker.com/compose/install/), [allowing non-root users](https://www.thegeekdiary.com/run-docker-as-a-non-root-user/)

**Then, install barge.** Open a new console and...

```console
# Grab repo
git clone https://github.com/oceanprotocol/barge
cd barge

# Clean up previous Ocean-related dirs & containers (optional but recommended) 
rm -rf ~/.ocean
./cleanup.sh
docker system prune -a --volumes
```

**Then, get Docker running.** To run barge, you need the Docker engine running. Here's how:
- If you're on Linux: you're good, there's nothing extra to do

Congrats! Barge is installed and ready to be run.

The sections below describe different ways to run barge. They're for reference only; DO NOT run them right now. Each README will describe what to do.

## Barge Basic

Barge with basic Predictoor components is:
- local chain (ganache)
- predictoor-related smart contracts deployed to chain

To run this, go to the barge console and:
```console
./start_ocean.sh --no-provider --no-dashboard --predictoor --with-thegraph
```

When barge runs, it will auto-publish DT3 tokens. Currently this is {`BTC/USDT`, Binance, 5min}, {`ETH/USDT`, Kraken, 5min} and {`XRP/USDT`, Binance, 5min}.

## Barge One Agent

Barge can run with any subset of the agents.

For example, to run barge with just trueval agent:
```console
./start_ocean.sh --no-provider --no-dashboard --predictoor --with-thegraph --with-pdr-trueval
```

## Barge All Agents

To run with all agents:

```console
./start_ocean.sh --no-provider --no-dashboard --predictoor --with-thegraph --with-pdr-trueval --with-pdr-trader --with-pdr-predictoor --with-pdr-publisher --with-pdr-dfbuyer
```

This will run all of the following at once:
- local chain (ganache)
- predictoor-related smart contracts deployed to chain
- trueval agent
- trader agent
- predictoor agent
- dfbuyer agent

## Change Barge Itself

Some subcomponents of Barge are those from pdr-backend. If you change those components, then the new behavior becomes part of Barge upon the next Github Release of pdr-backend. See [release-process.md](release-process.md) Docker / Barge section for details.

For each other subcomponent of Barge, you need to change its respective repo similarly.

And for Barge core functionality, make changes to the [barge repo](https://github.com/oceanprotocol/barge) itself.

More info: [Barge flow of calls](barge-calls.md)

## All Barge READMEs

- [barge.md](barge.md): the main Barge README
- [barge-calls.md](barge-calls.md): order of execution from Barge and pdr-backend code
- [release-process.md](release-process.md): pdr-backend Dockerhub images get published with each push to `main`, and sometimes other branches. In turn these are used by Barge.
