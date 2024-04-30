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

#add pwd to bash path
export PATH=$PATH:.
```

You need a local copy of Ocean contract addresses [`address.json`](https://github.com/oceanprotocol/contracts/blob/main/addresses/address.json). In console:
```console
# make directory if needed
mkdir -p ~/.ocean; mkdir -p ~/.ocean/ocean-contracts; mkdir -p ~/.ocean/ocean-contracts/artifacts/

# copy from github to local directory. Or, use wget if Linux. Or, download via browser.
curl https://github.com/oceanprotocol/contracts/blob/main/addresses/address.json -o ~/.ocean/ocean-contracts/artifacts/address.json
```

If you're running MacOS, then in console:

```console
codesign --force --deep --sign - venv/sapphirepy_bin/sapphirewrapper-arm64.dylib
```

## Simulate Modeling and Trading

Simulation allows us to quickly build intuition, and assess the performance of the data / predicting / trading strategy (backtest).

Copy [`ppss.yaml`](../ppss.yaml) into your own file `my_ppss.yaml` and change parameters as you see fit.

```console
cp ppss.yaml my_ppss.yaml
```

Let's run the simulation engine. In console:
```console
pdr sim my_ppss.yaml
```

What the engine does does:
1. Set simulation parameters.
1. Grab historical price data from exchanges and stores in `parquet_data/` dir. It re-uses any previously saved data.
1. Run through many 5min epochs. At each epoch:
   - Build a model
   - Predict
   - Trade
   - Log to console and `logs/out_<time>.txt`
   - For plots, output state to `sim_state/`

Let's visualize results. Open a separate console, and:
```console
cd ~/code/pdr-backend # or wherever your pdr-backend dir is
source venv/bin/activate

#start the plots server
sim_plots
```

The plots server will give a url, such as [http://127.0.0.1:8050](http://127.0.0.1:8050). Open that url in your browser to see plots update in real time.

"Predict" actions are _two-sided_: it does one "up" prediction tx, and one "down" tx, with more stake to the higher-confidence direction. Two-sided is more profitable than one-sided prediction.

By default, simulation uses a linear model inputting prices of the previous 2-10 epochs as inputs (autoregressive_n), just BTC close price as input, a simulated 0% trading fee, and a trading strategy of "buy if predict up; sell 5min later". You can play with different values in `my_ppss.yaml`.

Profit isn't guaranteed: fees, slippage and more eats into them. Model accuracy makes a big difference too.

To see simulation CLI options: `pdr sim -h`.

Simulation uses Python [logging](https://docs.python.org/3/howto/logging.html) framework. Configure it via [`logging.yaml`](../logging.yaml). [Here's](https://medium.com/@cyberdud3/a-step-by-step-guide-to-configuring-python-logging-with-yaml-files-914baea5a0e5) a tutorial on yaml settings.

By default, Dash plots the latest sim (even if it is still running). To enable plotting for a specific run, e.g. if you used multisim or manually triggered different simulations, the sim engine assigns unique ids to each run.
Select that unique id from the `sim_state` folder, and run `sim_plots --run_id <unique_id>` e.g. `sim_plots --run_id 97f9633c-a78c-4865-9cc6-b5152c9500a3`

You can run many instances of Dash at once, with different URLs. To run on different ports, use the `--port` argument.

## Run Trader Bot on Sapphire Testnet

Predictoor contracts run on [Oasis Sapphire](https://docs.oasis.io/dapp/sapphire/) testnet and mainnet. Sapphire is a privacy-preserving EVM-compatible L1 chain.

Let's get our bot running on testnet first.

First, tokens! You need (fake) ROSE to pay for gas, and (fake) OCEAN to stake and earn. [Get them here](testnet-faucet.md).

Then, copy & paste your private key as an envvar. In console:

```console
export PRIVATE_KEY=<YOUR_PRIVATE_KEY>
```

Then, run a simple trading bot. In console:

```console
pdr trader 2 my_ppss.yaml sapphire-testnet
```

Your bot is running, congrats! Sit back and watch it in action.

It logs to console, and to `logs/out_<time>.txt`. Like simulation, it uses Python logging framework, configurable in `logging.yaml`.

To see trader CLI options: `pdr trader -h`

You can track behavior at finer resolution by writing more logs to the [code](../pdr_backend/trader/trader_agent.py), or [querying Predictoor subgraph](subgraph.md).

## Run Trader Bot on Sapphire Mainnet

Time to make it real: let's get our bot running on Sapphire _mainnet_.

First, real tokens! Get [ROSE via this guide](get-rose-on-sapphire.md) and [OCEAN via this guide](get-ocean-on-sapphire.md).

Then, copy & paste your private key as an envvar. (You can skip this if it's same as testnet.) In console:

```console
export PRIVATE_KEY=<YOUR_PRIVATE_KEY>
```

Update `my_ppss.yaml` as desired.

Then, run the bot. In console:

```console
pdr trader 2 my_ppss.yaml sapphire-mainnet
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

## Run Bots Remotely

To scale up compute or run without tying up your local machine, you can run bots remotely. Get started [here](remotebot.md).

## Run Local Network

To get extra-fast block iterations, you can run a local test network (with local bots). It does take a bit more up-front setup. Get started [here](barge.md).

## Warning

You will lose money trading if your $ out exceeds your $ in. Do account for trading fees, order book slippage, cost of prediction feeds, and more. Everything you do is your responsibility, at your discretion. None of this repo is financial advice.
