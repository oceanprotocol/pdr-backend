<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# About Dynamic Model Codebase

This README describes the structure of the code that does dynamic modeling, and simulation of modeling & trading. It's at `pdr_backend/predictoor/approach3/`.

Two flows use the code:
1. Simulation of modeling & trading
2. Run predictoor bot

Contents of this README:
- [Code and simulation](#code-and-simulation)
- [Code and predictoor bot](#code-and-predictoor-bot)
- [Description of each approach3 file](#description-of-each-approach3-file)

## Code and Simulation

The simulation flow is used by [predictoor.md](predictoor.md) and [trader.md](trader.md).

Simulation is invoked by: `python pdr_backend/predictoor/approach3/runtrade.py`

What `runtrade.py` does:
- Set simulation parameters.
- Grab historical price data from exchanges and stores in `csvs/` dir. It re-uses any previously saved data.
- Run through many 5min epochs. At each epoch:
   - Build a model
   - Predict up/down
   - Trade.
   - (It logs this all to screen, and to `out*.txt`.)
- Plot total profit versus time.

When doing simulations:
- You can plot more things by uncommenting the `plot*` commands at the bottom of [trade_engine.py](../pdr_backend/predictoor/approach3/trade_engine.py)


## Code and predictoor bot

The predictoor bot flow is used by [predictoor.md](predictoor.md).

The bot is invoked by: `python pdr_backend/predictoor/main.py 3`

- It runs [`predictoor_agent3.py::PredictoorAgent3`](../pdr_backend/predictoor/approach3/predictoor_agent3.py) found in `pdr_backend/predictoor/approach3`
- It's configured by envvars and [`predictoor_config3.py::PredictoorConfig3`](../pdr_backend/predictoor/approach3/predictoor_config3.py)
- It predicts according to `PredictoorAgent3:get_prediction()`.

## Description of each approach3 file

The code is at [pdr_backend/predictoor/approach3/](../pdr_backend/predictoor/approach3/).

**Do simulation, including modeling & trading:**
- `runtrade.py` - top-level file to invoke trade engine
- `trade_engine.py` - simple, naive trading engine
- `tradeutil.py` - utilities used by trading
- `plotutil.py` - utilities for plotting from simulations

**Build & use predictoor bot:**
- `predictoor_agent3.py` - main agent. Builds model
- `predictoor_config3.py` - solution strategy parameters for the bot

**Build & use the model:** (used by simulation and bot)
- `model_factory.py` - converts X/y data --> AI/ML model
- `model_ss.py` - solution strategy parameters for model_factory
- `prev_model.py` - a very simple model that predict's "yesterday's weather"

**Build & use data:** (used by model)
- `data_factory.py` - converts historical data -> historical dataframe -> X/y model data
- `data_ss.py` - solution strategy parameters for data_factory
- `pdutil.py` - utilities for (pandas) data frames

**Time utilities:** (used by data)
- `timeblock.py` - utility to convert a single time-series into a 2d array, to be part of the X input to modeling training inference
- `timeutil.py` - utilities to convert among different time units

**Other utilities:**
- `constants.py` - basic constants
- `test/test*.py` - unit tests for each py file

