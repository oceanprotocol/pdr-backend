<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# About Dynamic Model Codebase

This README describes the structure of the code that does dynamic modeling, and simulation of modeling & trading. It's at [`pdr_backend/predictoor/approach3/`](../pdr_backend/predictoor/approach3/).

Two flows use the code:
1. Simulation of modeling & trading
2. Run predictoor bot

Contents of this README:
- [Code and Simulation](#code-and-simulation)
- [Code and Predictoor bot](#code-and-predictoor-bot)
- [Description of each file](#description-of-each-approach3-file)
- [HOWTO](#howtos) add new data, change model, etc

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

The code is at [`pdr_backend/predictoor/approach3/`](../pdr_backend/predictoor/approach3/).

**Do simulation, including modeling & trading:**
- [`runtrade.py`](../pdr_backend/predictoor/approach3/runtrade.py) - top-level file to invoke trade engine
- [`trade_engine.py`](../pdr_backend/predictoor/approach3/trade_engine.py) - simple, naive trading engine
- [`tradeutil.py`](../pdr_backend/predictoor/approach3/tradeutil.py) - trade engine parameters, trading strategy parameters, and utilities for trading
- [`plotutil.py`](../pdr_backend/predictoor/approach3/plotutil.py) - utilities for plotting from simulations

**Build & use predictoor bot:**
- [`predictoor_agent3.py`](../pdr_backend/predictoor/approach3/predictoor_agent3.py) - main agent. Builds model
- [`predictoor_config3.py`](../pdr_backend/predictoor/approach3/predictoor_config3.py) - solution strategy parameters for the bot

**Build & use the model:** (used by simulation and bot)
- [`model_factory.py`](../pdr_backend/predictoor/approach3/model_factory.py) - converts X/y data --> AI/ML model
- [`model_ss.py`](../pdr_backend/predictoor/approach3/model_ss.py) - solution strategy parameters for model_factory
- [`prev_model.py`](../pdr_backend/predictoor/approach3/prev_model.py) - a very simple model that predict's "yesterday's weather"

**Build & use data:** (used by model)
- [`data_factory.py`](../pdr_backend/predictoor/approach3/data_factory.py) - converts historical data -> historical dataframe -> X/y model data
- [`data_ss.py`](../pdr_backend/predictoor/approach3/data_ss.py) - solution strategy parameters for data_factory, ie sets what data to use
- [`pdutil.py`](../pdr_backend/predictoor/approach3/pdutil.py) - utilities for (pandas) data frames

**Time utilities:** (used by data)
- [`timeblock.py`](../pdr_backend/predictoor/approach3/timeblock.py) - utility to convert a single time-series into a 2d array, to be part of the X input to modeling training inference
- [`timeutil.py`](../pdr_backend/predictoor/approach3/timeutil.py) - utilities to convert among different time units

**Other utilities:**
- [`constants.py`](../pdr_backend/predictoor/approach3/constants.py) - basic constants
- [`test/test*.py`](../pdr_backend/predictoor/approach3/test/) - unit tests for each py file

## HOWTOs

### HOWTOs: Flows

**HOWTO change parameters for the simulation**
- Almost every line of [`runtrade.py`](../pdr_backend/predictoor/approach3/runtrade.py) is changeable :)
- You can change training data, model, etc according to the HOWTOs

**HOWTO change parameters for the predictoor Bot**
- Almost every line of [`runtrade.py`](../pdr_backend/predictoor/approach3/runtrade.py) is changeable :)
- You can change training data, model, etc according to the HOWTOs

### HOWTOs: Specific training data, model, etc

**HOWTO set what training data to use:** 
- Change arguments to [`data_ss.py:DataSS()`](../pdr_backend/predictoor/approach3/data_ss.py) constructor.
- Includes: how far to look back historically for training samples, max # training samples, how far to look back when making a single inference.

**HOWTO set what model to use:** 
- Change argument to [`model_ss.py:ModelSS()`](../pdr_backend/predictoor/approach3/model_ss.py)] constructor.
- Includes just: the model. "LIN" = linear.

**HOWTO set trade parameters (uncontrollable by trader):** 
- Change arguments to [`tradeutil.py:TradeParams()`](../pdr_backend/predictoor/approach3/tradeutil.py)] constructor.
- Includes: % trading fee, and initial trader holdings.

**HOWTO set trade strategy (controllable by trader):** 
- Change arguments to [`tradeutil.py:TradeSS()`](../pdr_backend/predictoor/approach3/tradeutil.py)] constructor.
- Includes: how much $ to trade with at each point, where to log, whether to plot

