<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Run a Trader Bot

This README takes shows how to earn $ by running a trader bot on mainnet, and beyond.

1. **[Install](#install-pdr-backend-repo)**
1. **[Simulate modeling & trading](#simulate-modeling-and-trading)**
1. **[Run bot on testnet](#run-trader-bot-on-sapphire-testnet)**
1. **[Run bot on mainnet](#run-trader-bot-on-sapphire-mainnet)**

Then, you can [go beyond](#go-beyond): [optimize trading strategy](#optimize-trading-strategy), and more.

## Install pdr-backend Repo

In a new console:

```console
# clone the repo and enter into it
git clone https://github.com/oceanprotocol/pdr-backend
cd pdr-backend

# Create & activate virtualenv
python -m venv venv
source venv/bin/activate

# Install modules in the environment
pip install -r requirements.txt
```

If you're running MacOS, then in console:
```console
codesign --force --deep --sign - venv/sapphirepy_bin/sapphirewrapper-arm64.dylib
```

## Simulate Modeling and Trading

Simulation allows us to quickly build intuition, and assess the performance of the data / model / trading strategy (backtest).

Let's simulate! In console:
```console
python pdr_backend/simulation/runtrade.py
```

What `runtrade.py` does:
1. Set simulation parameters.
1. Grab historical price data from exchanges and stores in `csvs/` dir. It re-uses any previously saved data.
1. Run through many 5min epochs. At each epoch:
   - Build a model
   - Predict up/down
   - Trade.
   - (It logs this all to screen, and to `out*.txt`.)
   - Plot total profit versus time.

The baseline settings use a linear model inputting prices of the previous 10 epochs as inputs, a simulated 0% trading fee, and a trading strategy of "buy if predict up; sell 5min later". You can play with different values in [runtrade.py](../pdr_backend/simulation/runtrade.py).

Profit isn't guaranteed: fees, slippage and more eats into them. Model accuracy makes a huge difference too.

([This README](dynamic-model-codebase.md) has more info about the simulator's code structure.)

## Run Trader Bot on Sapphire Testnet

Predictoor contracts run on [Oasis Sapphire](https://docs.oasis.io/dapp/sapphire/) testnet and mainnet. Sapphire is a privacy-preserving EVM-compatible L1 chain.

Let's get our bot running on testnet first.

First, tokens! You need (fake) ROSE to pay for gas, and (fake) OCEAN to stake and earn. [Get them here](testnet-faucet.md).

Then, copy & paste your private key as an envvar. In console:
```console
export PRIVATE_KEY=<YOUR_PRIVATE_KEY>
```

Now, set other envvars. In console:
```console
#other envvars for testnet and mainnet
export ADDRESS_FILE="${HOME}/.ocean/ocean-contracts/artifacts/address.json"
export PAIR_FILTER=BTC/USDT
export TIMEFRAME_FILTER=5m
export SOURCE_FILTER=binance

#testnet-specific envvars
export RPC_URL=https://testnet.sapphire.oasis.dev
export SUBGRAPH_URL=https://v4.subgraph.sapphire-testnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph
export STAKE_TOKEN=0x973e69303259B0c2543a38665122b773D28405fB # (fake) OCEAN token address
export OWNER_ADDRS=0xe02a421dfc549336d47efee85699bd0a3da7d6ff # OPF deployer address
```

([envvars.md](envvars.md) has details.)

Then, run a simple trading bot. In console:
```console
python pdr_backend/trader/main.py
```

Your bot is running, congrats! Sit back and watch it in action. 

(You can track at finer resolution by writing more logs to the [code](../pdr_backend/trader/trader_agent.py), or [querying Predictoor subgraph](subgraph.md).)

## Run Trader Bot on Sapphire Mainnet

Time to make it real: let's get our bot running on Sapphire _mainnet_.

First, real tokens! Get [ROSE via this guide](get-rose-on-sapphire.md) and [OCEAN via this guide](get-ocean-on-sapphire.md).

Then, copy & paste your private key as an envvar. (You can skip this if it's same as testnet.) In console:
```console
export PRIVATE_KEY=<YOUR_PRIVATE_KEY>
```

Now, set other envvars. In console:
```console
#envvars for testnet and mainnet
#(can skip this, since same as testnet)

#mainnet-specific envvars
export RPC_URL=https://sapphire.oasis.io
export SUBGRAPH_URL=https://v4.subgraph.sapphire-mainnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph
export STAKE_TOKEN=0x39d22B78A7651A76Ffbde2aaAB5FD92666Aca520 # OCEAN token address
export OWNER_ADDRS=0x4ac2e51f9b1b0ca9e000dfe6032b24639b172703 # OPF deployer address
```

Then, run the bot. In console:
```console
python pdr_backend/trader/main.py
```

This is where there's real $ at stake. Good luck!

Track performance, as in testnet.

# Go Beyond

You've gone through all the essential steps to earn $ by running a trader bot on mainnet.

The next sections describe how to go beyond, by optimizing the trading strategy and more.

## Optimize Trading Strategy

Once you're familiar with the above, you can set your own trading strategy and optimize it for $. Here's how:
1. Fork `pdr-backend` repo.
1. Change trader bot code as you wish, while iterating with simulation.
1. Bring your trader bot to testnet then mainnet.

To help, here's the code structure of the bot:
- It runs [`trader_agent.py::TraderAgent`](../pdr_backend/trader/trader_agent.py) found in `pdr_backend/trader/`
- It's configured by envvars and [`trader_config.py::TraderConfig`](../pdr_backend/trader/trader_config.py)

## Run Bots Remotely

To scale up compute or run without tying up your local machine, you can run bots remotely. Get started [here](remotebot.md).

## Run Local Network

To get extra-fast block iterations, you can run a local test network (with local bots). It does take a bit more up-front setup. Get started [here](barge.md).

## Warning

You will lose money trading if your $ out exceeds your $ in. Do account for trading fees, order book slippage, cost of prediction feeds, and more. Everything you do is your responsibility, at your discretion. None of this repo is financial advice.
