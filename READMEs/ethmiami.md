<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# ETHMiami: Accurate ETH Predictoor

## Introduction

This README provides instructions for the ETHMiami data science competition run by Ocean Protocol, Oct 27-29, 2023.

The goal is to accurately predict whether ETH with rise or fall, every five minutes, over an 8-hour interval.

Through this README, you're supplied with:
- A baseline approach to gather data and build an AI/ML prediction model
- A "simulation flow" to quickly test performance, enabling rapid looping to improve the model
- A "predictoor bot flow" that uses the model to submit predictions to the chain every 5 minutes

The competition is run on [Oasis Sapphire testnet](https://docs.oasis.io/dapp/sapphire/).

Bonus! You can use the outcome from this competition to run [your own predictoor bot](predictoor.md) bot on Oasis Sapphire _mainnet_, to earn real $ in the Ocean Predictoor ecosystem.

### Key Parameters

Criteria / prizes:
- Accuracy = % correct predictions in the interval
- 1st place: (FIXME) OCEAN -> highest accuracy
- 2nd place: (FIXME) OCEAN -> 2nd highest accuracy
- 3rd place: (FIXME) OCEAN -> 3rd highest accuracy

Timing:
- Your predictoor must make submissions **every 5 minutes** in the interval from **4:00am to 12:00pm EDT on Sun Oct 29**.
- It's ok if it predicts before or after too! But those won't be counted
- For each 5-min slot that it neglects to submit a prediction, that miss is treated as an incorrect prediction (vs being ignored)

### 0.4 Support

If you encounter issues, feel free to reach out :raised_hand:

- Ask someone from the Ocean core team who will be physically present at the hackathon
- Ask in [Ocean #predictoor Discord](https://discord.com/channels/612953348487905282/1151066755796574389).

### Outline of this README

This README shows how to line up an AI/ML model-testing flow, then run a predictoor bot on testnet.

Here are the steps:

1. **[Install pdr-backend repo](#install-pdr-backend-repo)**
1. **[Try out simulation flow (modeling & trading)](#try-out-simulation-flow)**
1. **[Try out bot flow on testnet](#try-out-bot-flow)**
1. **[Improve model: looping in simulation flow](#improve-model)**
1. **[Submit to competion: Run bot in time for deadline](#run-bot-for-real)**

You'll want to go through steps (1)-(3) quickly in case of snags. You'll spend most time in (4) flexing your data science muscles. Finally, put your work to the test in (5).

After the interval completes, the judges will run a script to compute the accuracy of each team's predictoor bot. And you'll hear how you did.

## Install pdr-backend repo

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

## Try out simulation flow

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

(The "improve model" section below describes how to change the data, modeling approach, etc.)

## Try out bot flow

In this step, you'll try out the "predictoor bot flow", so that when it comes time to submit using the bot flow, you'll be ready. Every five minutes, the bot builds a new model, predicts, then submits the prediction to chain.

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
export SOURCE_FILTER=binanceus

#testnet-specific envvars
export RPC_URL=https://testnet.sapphire.oasis.dev
export SUBGRAPH_URL=https://v4.subgraph.sapphire-testnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph
export STAKE_TOKEN=0x973e69303259B0c2543a38665122b773D28405fB # (fake) OCEAN token address
export OWNER_ADDRS=0xe02a421dfc549336d47efee85699bd0a3da7d6ff # OPF deployer address
```

([envvars.md](envvars.md) has details.)

Then, run your predictoor bot. In console:
```console
python pdr_backend/predictoor/main.py 3
```

Your bot is running, congrats! Sit back and watch it in action. It will loop continuously.
- It has behavior to maximize accuracy without missing submission deadlines, as follows. 60 seconds before predictions are due, it will build a model then submit a prediction. It will repeat submissions every few seconds until the deadline.
- It does this for every 5-minute epoch.

(You can track at finer resolution by writing more logs to the [code](../pdr_backend/predictoor/approach3/predictoor_agent3.py), or [querying Predictoor subgraph](subgraph.md).)

## Improve model

This is the fun part! The game is to improve model accuracy with the help of the "simulation flow" presented above.

The baseline model is linear, inputting prices of the previous 10 epochs as inputs. (There's a reference trading of "buy if predict up; sell 5min later", but note that your focus is accuracy.)

What you'll be doing:
- Change values in [runtrade.py](../pdr_backend/predictoor/approach3/runtrade.py) and elsewhere to choose: what input data to use, how to process the input data, what modeling approach to use, and more.
- Run the simulation, and see how well it does
- Repeat!

You'll want to understand how to work with the simulation & modeling codebase. Please go **[here](dynamic-model-codebase.md)** to learn more. Like any code, it will take some effort for you to understand. Don't be scared of it! The better you know it, the better your accuracy:)

Have fun!

And don't forget to do the final step: running your bot for real.

## Run bot for real

Let's put all your hard work to the test: follow the "bot flow" provided above. But now it should be running _your_ setup from the previous step, having with more accurate predictions.

⚠️ The simulation flow and bot flow have different places to set some parameters: simulation uses `runtrade.py`, and bot uses `predictoor_config3.py`. [Here are details](dynamic-model-codebase.md). So, make sure that your bot flow has the parameters you want.

That's it! Take some time off while the time interval passes and your bot does its thing.
