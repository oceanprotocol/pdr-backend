<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Run a Predictoor Bot

This README shows how to earn $ by running a predictoor bot on mainnet.

1. **[Install](#install-pdr-backend-repo)**
1. **[Simulate modeling & trading](#simulate-modeling-and-trading)**
1. **[Run bot on testnet](#run-predictoor-bot-on-sapphire-testnet)**
1. **[Run bot on mainnet](#run-predictoor-bot-on-sapphire-mainnet)**
1. **[Claim payout](#claim-payout)**
1. **[Check performance](#check-performance)**

Then, you can [go beyond](#go-beyond): [optimize model](#optimize-model), [run >1 bots](#run-many-bots-at-once), and more.


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
   - Plot total profit versus time.
   - (It logs this all to screen, and to `out*.txt`.)

The baseline settings use a linear model inputting prices of the previous 10 epochs as inputs, a simulated 0% trading fee, and a trading strategy of "buy if predict up; sell 5min later". You can play with different values in [runtrade.py](../pdr_backend/simulation/runtrade.py).

Profit isn't guaranteed: fees, slippage and more eats into them. Model accuracy makes a huge difference too.

([This README](dynamic-model-codebase.md) has more info about the simulator's code structure.)

## Run Predictoor Bot on Sapphire Testnet

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

Then, run a bot with modeling-on-the fly (approach 3). In console:
```console
python pdr_backend/predictoor/main.py 3
```

Your bot is running, congrats! Sit back and watch it in action. It will loop continuously.
- It has behavior to maximize accuracy without missing submission deadlines, as follows. 60 seconds before predictions are due, it will build a model then submit a prediction. It will repeat submissions every few seconds until the deadline.
- It does this for every 5-minute epoch.

(You can track at finer resolution by writing more logs to the [code](../pdr_backend/predictoor/approach3/predictoor_agent3.py), or [querying Predictoor subgraph](subgraph.md).)


## Run Predictoor Bot on Sapphire Mainnet

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
python pdr_backend/predictoor/main.py 3
```

This is where there's real $ at stake. Good luck!

Track performance, as in testnet.

## Claim Payout

When running predictoors on mainnet, you have the potential to earn $.

**[Here](payout.md)** are instructions to claim your earnings.

## Check Performance

After you run your bot and claimed the payout, you might want to check how your bot is perfoming before you start improving it.

Follow **[this instructions](predictoor-data.md)** to get an overview of your performance so far.

# Go Beyond

You've gone through all the essential steps to earn $ by running a predictoor bot on mainnet.

The next sections describe how to go beyond, by optimizing the model and more.

## Optimize Model

Once you're familiar with the above, you can make your own model and optimize it for $. Here's how:
1. Fork `pdr-backend` repo.
1. Change predictoor approach3 modeling code as you wish, while iterating with simulation.
1. Bring your model as a Predictoor bot to testnet then mainnet.


([This README](dynamic-model-codebase.md) has more info about the simulator's code structure.)


## Run Many Bots at Once

[PM2](https://pm2.keymetrics.io/docs/usage/quick-start/) is "a daemon process manager that will help you manage and keep your application online."

This section shows first how to use PM2 to run one bot on testnet. It then shows how to extend this to mainnet, and many bots at once.

First, install PM2: `npm install pm2 -g`

Then, prepare the PM2 config file:
- Skim over [`pm2-testnet-predictoor.config.js`](../pm2-testnet-predictoor.config.js). It names the script, and sets envvars like we did above, but automatically.
- Open the local version of this file. It's in the root of your `pdr-backend/` directory. In the file, set `YOUR_PRIVATE_KEY`.

Now, run the bot with PM2. In console:
```console
pm2 start pm2-testnet-predictoor.config.js
```

Your bot's running on testnet again! This time with the help of PM2.

Next, monitor the logs: `pm2 logs pm2-testnet-predictoor` (ctrl-c to stop)

Finally, stop the bot: `pm2 stop pm2-testnet-predictoor`

Congrats! You've used PM2 to start, monitor, and stop a bot on testnet.

To run on _mainnet_: it's a mainnet config file [`pm2-mainnet-predictoor.config.js`](../pm2-mainnet-predictoor.config.js). It's like testnet, with different envvars. Work with the local version of this file.

To run 20 bots: alter the config file as needed. Or, have 20 config files.

Other interesting PM2 commands:
- List all running processes: `pm2 ls`
- Stop process with id=0: `pm2 stop 0 # (similar for other cmds)`
- Stop all processes: `pm2 stop all`
- Top-level help: `pm2 help`
- Help for "start" command: `pm2 help start # (similar for other cmds)`
- More yet: **[PM2 docs](https://pm2.keymetrics.io/docs/usage/quick-start/)**

## Run Bots Remotely

To scale up compute or run without tying up your local machine, you can run bots remotely. Get started [here](remotebot.md).

## Run Local Network

To get extra-fast block iterations, you can run a local test network (with local bots). It does take a bit more up-front setup. Get started [here](barge.md).

## Other READMEs

- [Root README](../README.md)

## Warning

You will lose money as a predictoor if your $ out exceeds your $ in. If you have low accuracy you’ll have your stake slashed a lot. Do account for gas fees, compute costs, and more. Everything you do is your responsibility, at your discretion. None of this repo is financial advice.
