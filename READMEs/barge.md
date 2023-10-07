<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Barge

## Contents

Installation
- [Install Barge](#install-barge)
- [Potential Issues](#potential-issues)
- [Run Docker](#run-docker)

Reference: how to run barge with...
- [No agents](#barge-basic) - just ganache chain & predictoor contracts
- [One agent](#barge-one-agent) - eg trueval agent
- [All agents](#barge-all-agents) - predictoor, trader, trueval, dfbuyer


## Install Barge

- Pre-requisites: [Docker](https://docs.docker.com/engine/install/), [Docker Compose](https://docs.docker.com/compose/install/), [allowing non-root users](https://www.thegeekdiary.com/run-docker-as-a-non-root-user/)

In a new console:

```console
# Grab repo
git clone https://github.com/oceanprotocol/barge
cd barge
git checkout predictoor

# (optional) Clean up previous Ocean-related dirs & containers
rm -rf ~/.ocean
./cleanup.sh
docker system prune -a --volumes
```

The sections below describe different ways to run barge. They're for reference only; DO NOT run them right now. Each README will describe what to do.

## Potential Issues

Issue: MacOS * Docker 
- On MacOS, Docker may freeze. Fix by reverting to 4.22.1. Details follow.
- Symptoms: it stops logging; Docker cpu usage is 0%; it hangs when you type `docker ps` in console
- For us: Docker 4.24.1 (released Sep 28, 2023) freezes, and 4.22.1 works. [Docker release notes](https://docs.docker.com/desktop/release-notes).
- To fix:
  - In console: `./cleanup.sh; docker system prune -a --volumes`
  - Download [Docker 4.22.1](https://docs.docker.com/desktop/release-notes/#4221)
  - Open the download, drag "Docker" to "Applications"
  - Chose to "Replace" the existing installation
  - Run Docker desktop. Confirm the version via "About".
  - If that doesn't work, then [fully uninstall Docker](https://www.makeuseof.com/how-to-uninstall-docker-desktop-mac/) and try again.

## Run Docker

To run barge, you need the Docker engine running. 

If you're on Linux: you're good, there's nothing extra to do.

If MacOS: 
- via console: `open -a Docker`
- or, via app: open Finder app, find Docker, click it

## Barge Basic

Barge with basic Predictoor components is:
- local chain (ganache)
- predictoor-related smart contracts deployed to chain

To run this, go to the barge console and:
```console
./start_ocean.sh --no-aquarius --no-elasticsearch --no-provider --no-dashboard --predictoor --with-thegraph
```

When barge runs, it will auto-publish DT3 tokens. Currently this is {`BTC/TUSD`, Binance, 5min}, {`ETH/USDT`, Kraken, 5min} and {`XRP/USDT`, Binance, 5min}.

## Barge One Agent

Barge can run with any subset of the agents.

For example, to run barge with just trueval agent:
```console
./start_ocean.sh --no-aquarius --no-elasticsearch --no-provider --no-dashboard --predictoor --with-thegraph --with-pdr-trueval
```

## Barge All Agents

To run with all agents:

```console
./start_ocean.sh --no-aquarius --no-elasticsearch --no-provider --no-dashboard --predictoor --with-thegraph --with-pdr-trueval --with-pdr-trader --with-pdr-predictoor --with-pdr-publisher --with-pdr-dfbuyer
```

This will run all of the following at once:
- local chain (ganache)
- predictoor-related smart contracts deployed to chain
- trueval agent
- trader agent
- predictoor agent
- dfbuyer agent

