<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# About Dynamic Model Codebase

Dynamic modeling is used in two places:

1. Simulation of modeling & trading -> [`pdr_backend/predictoor/simulation/`](../pdr_backend/predictoor/simulation/).
2. Run predictoor bot - [`pdr_backend/predictoor/approach3/`](../pdr_backend/predictoor/approach3/)

Contents of this README:
- [Code and Simulation](#code-and-simulation)
- [Code and Predictoor bot](#code-and-predictoor-bot)
- [Description of each file](#description-of-files)
- [HOWTO](#howtos) add new data, change model, etc

## Code and Simulation

The simulation flow is used by [predictoor.md](predictoor.md) and [trader.md](trader.md).

Simulation is invoked by: `python pdr_backend/predictoor/simulation/runtrade.py`

What `runtrade.py` does:
- Set simulation parameters.
- Grab historical price data from exchanges and stores in `csvs/` dir. It re-uses any previously saved data.
- Run through many 5min epochs. At each epoch:
   - Build a model
   - Predict up/down
   - Trade.
   - (It logs this all to screen, and to `out*.txt`.)
   - Plot total profit versus time, more

## Code and predictoor bot

The predictoor bot flow is used by [predictoor.md](predictoor.md).

The bot is invoked by: `python pdr_backend/predictoor/main.py 3`

- It runs [`predictoor_agent3.py::PredictoorAgent3`](../pdr_backend/predictoor/approach3/predictoor_agent3.py) found in `pdr_backend/predictoor/approach3`
- It's configured by envvars and [`predictoor_config3.py::PredictoorConfig3`](../pdr_backend/predictoor/approach3/predictoor_config3.py)
- It predicts according to `PredictoorAgent3:get_prediction()`.

## Description of files

**Do simulation, including modeling & trading:**
- [`runtrade.py`](../pdr_backend/simulation/runtrade.py) - top-level file to invoke trade engine
- [`trade_engine.py`](../pdr_backend/simulation/trade_engine.py) - simple, naive trading engine

**Build & use predictoor bot:**
- [`predictoor_agent3.py`](../pdr_backend/predictoor/approach3/predictoor_agent3.py) - main agent. Builds model
- [`predictoor_config3.py`](../pdr_backend/predictoor/approach3/predictoor_config3.py) - solution strategy parameters for the bot

**Build & use the model:** (used by simulation and bot)
- [`model_factory.py`](../pdr_backend/model_eng/model_factory.py) - converts X/y data --> AI/ML model
- [`model_ss.py`](../pdr_backend/model_eng/model_ss.py) - solution strategy parameters for model_factory

**Build & use data:** (used by model)
- [`data_factory.py`](../pdr_backend/data_eng/data_factory.py) - converts historical data -> historical dataframe -> X/y model data
- [`data_ss.py`](../pdr_backend/data_eng/data_ss.py) - solution strategy parameters for data_factory, ie sets what data to use

## HOWTOs

**On PP and SS:**
- This is a naming idiom that you'll see in in module names, class names, variable names
- "SS" = controllable by user, if in a real-world setting. "Solution Strategy"
- "PP" = uncontrollable by user "".

**HOWTO change parameters for each flow:**
- **For running simulation flow:** change lines in [`runtrade.py`](../pdr_backend/simulation/runtrade.py). Almost every line is changeable, to change training data, model, trade parameters, and trade strategy. Details on each below.
- **For running predictoor bot flow:** change [`predictoor_config3.py`](../pdr_backend/predictoor/approach3/predictoor_config3.py) solution strategy parameters for the bot

**HOWTO set what training data to use:** 
- Change args to `data_ss.py:DataSS()` constructor.
- Includes: how far to look back historically for training samples, max # training samples, how far to look back when making a single inference.

**HOWTO set what model to use:** 
- Change args to `model_ss.py:ModelSS()` constructor.
- Includes: the model. "LIN" = linear.

**HOWTO set trade parameters:** 
- Change args to `trade_pp.py:TradePP()` constructor.
- Includes: % trading fee

**HOWTO set trade strategy:** 
- Change args to `trade_ss.py:TradeSS()` constructor.
- Includes: how much $ to trade with at each point

**HOWTO set simulation strategy:** 
- Change args to `sim_ss.py:SimSS()` constructor.
- Includes: where to log, whether to plot

