<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Run Dynamic Model Predictoor

Here, we build models on-the-fly, ie dynamic models. It's `approach3` in `pdr-backend` repo.

Dynamic modeling means we don't need to save a model, manage it separately, or link from a different location; therefore it's easier than static models.

Steps:
1. [Develop & backtest dynamic models](#develop-and-backtest-models)
1. [Use model approach in Predictoor bot](#use-model-in-predictoor-bot)

_Both_ steps are performed using this repo.

Let's go through each step in turn.

## Develop and backtest models

Here, we develop & backtest the model. The setup is optimized for rapid iterations, by being independent of Barge and Predictoor bots.

In work console:
```console
#this dir will hold data fetched from exchanges (only needed once)
mkdir csvs

#run dynamic model unit tests
pytest pdr_backend/predictoor/approach3

#run dynamic model backtest. (Edit params in runtrade.py as you wish)
python pdr_backend/predictoor/approach3/runtrade.py
```

`runtrade.py` will grab data from exchanges, then simulate one epoch at a time (including building a model, predicting, and trading). When done, it plots accumulated returns vs. time. Besides logging to stdout, it also logs to out*.txt in pwd.

## Use model in Predictoor bot

Once you're satisfied with your backtests, you're ready to use dynamic modeling in a Predictoor bot.

First, get Barge & other bots going via instructions to run local network or otehrwise. The [parent predictoor README: predictoor.md](./predictoor.md) links to these.

Then, in work console:
```console
# run dynamic model predictoor bot
python pdr_backend/predictoor/main.py 3
```

That's it! You're running. (There are variants of the above using PM2, or on Azure, etc.)

Observe all bots in action:
- In the barge console: trueval bot submitting (mock random) truevals, trader is (mock) trading, etc
- In your work console: predictoor bot is submitting (mock random) predictions
- Query predictoor subgraph for detailed run info. [`subgraph.md`](subgraph.md) has details.

## Your own dynamic model

Once you're familiar with the above, you can make your own model: fork pdr-backend, and change the dynamic model code as you wish.

To help, here's the code structure:
- It runs [`predictoor_agent3.py::PredictoorAgent3`](../pdr_backend/predictoor/approach3/predictoor_agent3.py) found in `pdr_backend/predictoor/approach3`
- It's configured by envvars and [`predictoor_config3.py::PredictoorConfig3`](../pdr_backend/predictoor/approach3/predictoor_config3.py)
- It predicts according to `PredictoorAgent3:get_prediction()`.


## Other READMEs

- [Parent predictoor README: predictoor.md](./predictoor.md)
- [Root README](../README.md)
