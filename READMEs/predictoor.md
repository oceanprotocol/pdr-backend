<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Run a Predictoor Bot

This README takes you from zero to running a predictoor bot on mainnet, and beyond.

Toward running on mainnet:
1. **[Install](#install-pdr-backend-repo)**
1. **[Simulate modeling & trading](#simulate-modeling-and-trading)**
1. **[Run bot on testnet](#run-predictoor-bot-on-sapphire-testnet)**
1. **[Run bot on mainnet](##run-predictoor-bot-on-sapphire-mainnet)**

Going beyond: (Optional, in any order)
- **[Optimize model](#optimize-model)**
- **[Run >1 bots at once](#run-many-bots-at-once)**
- **[Run bots _remotely_](##run-bots-remotely)**

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
python pdr_backend/predictoor/approach3/runtrade.py
```

What `runtrade.py` does:
1. Set simulation parameters.
1. Grab historical price data from exchanges and stores in `csvs/` dir. It re-uses any previously saved data.
1. Run through many 5min epochs. At each epoch:
   - Build a model
   - Predict up/down
   - Trade.
   - (It logs this all to screen, and to `out*.txt`.)
1. Plot total profit versus time.

The baseline settings use a linear model inputting prices of the previous 10 epochs as inputs, a simulated 0% trading fee, and a trading strategy of "buy if predict up; sell 5min later". You can play with different values in [runtrade.py](../pdr_backend/predictoor/approach3/runtrade.py).

Profit isn't guaranteed: fees, slippage and more eats into them. Model accuracy makes a huge difference too.

You can plot more things by uncommenting the `plot*` commands at the bottom of [trade_engine.py](../pdr_backend/predictoor/approach3/trade_engine.py)

## Run Predictoor Bot on Sapphire Testnet

Predictoor contracts run on [Oasis Sapphire](https://docs.oasis.io/dapp/sapphire/) testnet and mainnet. Sapphire is a privacy-preserving EVM-compatible L1 chain.

Let's get our bot running on testnet first.

First, tokens! You need (fake) ROSE to pay for gas, and (fake) OCEAN to stake and earn. [Get them here](testnet-faucet.md).

Then, copy & paste your private key as an envvar. In console:
```console
export PRIVATE_KEY=<paste your PRIVATE_KEY here>
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

Then, run a bot with modeling-on-the fly (approach 3). In console:
```console
python pdr_backend/predictoor/main.py 3
```

Your bot is running, congrats! Sit back and watch it in action. It will loop continuously.
- It has behavior to maximize accuracy without missing submission deadlines, as follows. 60 seconds before predictions are due, it will build a model then submit a prediction. It will repeat submissions every few seconds until the deadline.
- It does this for every 5-minute epoch.

(You can track at finer resolution by adding more logs, or [querying Predictoor subgraph`](subgraph.md).)


## Run Predictoor Bot on Sapphire Mainnet

Time to make it real: let's get our bot running on Sapphire _mainnet_.

First, real tokens! Get [ROSE via this guide](get-rose-on-sapphire.md) and [OCEAN via this guide](get-ocean-on-sapphire.md).

Then, copy & paste your private key as an envvar. (You can skip this if it's same as testnet.) In console:
```console
export PRIVATE_KEY=<paste your PRIVATE_KEY here>
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
python pdr_backend/predictoor/main.py 3
```

This is where there's real $ at stake. Good luck!

Track performance, as in testnet.

The next sections describe how to go beyond this baseline of running a bot on mainnet.

## Optimize Model

Once you're familiar with the above, you can make your own model and optimize it for $. Here's how:
1. Fork `pdr-backend` repo
1. Change the approach3 modeling code as you wish, while iterating with simulation.
1. Bring your model as a Predictoor bot to testnet then Mainnet.

To help, here's the code structure of the bot:
- It runs [`predictoor_agent3.py::PredictoorAgent3`](../pdr_backend/predictoor/approach3/predictoor_agent3.py) found in `pdr_backend/predictoor/approach3`
- It's configured by envvars and [`predictoor_config3.py::PredictoorConfig3`](../pdr_backend/predictoor/approach3/predictoor_config3.py)
- It predicts according to `PredictoorAgent3:get_prediction()`.

### Run Many Bots at Once

(Stay tuned, this is coming:)

### Run bots Remotely

FIXME


## Other READMEs

- [Root README](../README.md)
