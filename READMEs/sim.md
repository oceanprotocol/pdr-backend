# Run sim/trading

Predict, trade, make $. Historical, live mock, or live real. This README shows how.

**Steps:**
1. **[Install](#1-install-pdr-backend-repo)**
1. **[Sim: mock trade on historical data](#2-sim-mock-trade-on-historical-data)**
1. **[Sim: mock trade on live data](#3-sim-mock-trade-on-live-data)**
1. **[Trade on live real data](#4-trade-on-live-real-data)**
1. **[Optimize profitability](#5-optimize-profitability)**

**Appendix: Dev Tools**
- **[Run pytest](#dev-run-pytest)**
- **[Run linters](#dev-run-linters)**
- **[Do performance profiling](#dev-do-performance-profiling)**
- **[Dependencies](#dev-dependencies)**


## 1. Install pdr-backend Repo

Prerequisites:
- Python 3.12. Earlier _will_ fail, e.g. can't find `UTC`. [Details](https://blog.miguelgrinberg.com/post/it-s-time-for-a-change-datetime-utcnow-is-now-deprecated)
- Ubuntu or MacOS. _Not_ Windows.


In a new console:

```console
# clone the repo and enter into it
git clone https://github.com/oceanprotocol/pdr-backend
cd pdr-backend

# create & activate virtualenv
python -m venv venv
source venv/bin/activate

# install modules in the environment
pip install -r requirements.txt

# add pwd to bash path
export PATH=$PATH:.
```

## 2. Sim: mock trade on historical data

Simulation allows us to quickly build intuition, and assess the performance of the data / predicting / trading strategy (backtest).

Copy [`ppss.yaml`](../ppss.yaml) into your own file `my_ppss.yaml` and change parameters as you see fit.

```console
cp ppss.yaml my_ppss.yaml
```

Be sure to set `tradetype` as `histmock`. This will simulate & mock-trade on historical data.

Let's run the engine! In console:
```console
pdr sim my_ppss.yaml
```

What the engine does:
1. Set sim parameters
2. Grab historical price data from exchanges and stores in `lake_data/` dir. It re-uses any previously saved data
3. Run through many 5 min epochs. At each epoch:
   - Build a model
   - Predict
   - Trade
   - Log (to console, and `logs/out_<time>.txt`)

To see sim options: `pdr sim -h`.

Sim uses Python [logging](https://docs.python.org/3/howto/logging.html) framework. Configure it via [`logging.yaml.`](../logging.yaml) [Learn more](https://medium.com/@cyberdud3/a-step-by-step-guide-to-configuring-python-logging-with-yaml-files-914baea5a0e5).


## 3. Sim: mock trade on live data

In my_ppss.yaml, set `tradetype` as `livemock`. This will simulate & mock-trade on _live_ data. Then, run the engine from console:

```console
pdr sim my_ppss.yaml
```


## 4. Trade on live real data


In my_ppss.yaml, set `tradetype` as `livereal`. This will trade _for real_ on _live_ data.  Then, run the engine from console:

```console
pdr sim my_ppss.yaml
```

Be careful, it's real $!


# 5. Optimize Profitability

Complementary strategies:
- Optimize data. Examples:
  - Train on longer history (must handle nonstationary though)
  - More features
  - more
- Optimize model. Examples:
  - Linear -> nonlinear
  - more
- Optimize trading. Examples:
  - Right-size trading: Kelly criterion
  - more

# Appendix: Dev Tools

## Dev: Run pytest

In console:

```console
# (ensure PRIVATE_KEY set as above)

# run a single test. The "-s" is for more output.
# note that pytest does dynamic type-checking too:)
pytest pdr_backend/util/test_noganache/test_util_constants.py::test_util_constants -s

# run all tests in a file
pytest pdr_backend/util/test_noganache/test_util_constants.py -s

# run all regular tests; see details on pytest markers to select specific suites
pytest
```

## Dev: Run linters

In console:

```console
# auto-fix some pylint complaints like whitespace. CI doesn't modify files; we do
black ./

# run linting on code style. Use same setup as CI
pylint --rcfile .pylintrc * pdr_backend/*

# mypy does static type-checking and more. Use same setup as CI
mypy --config-file mypy.ini ./
```


## Dev: do performance profiling

In console, run sim with profiling:

```console
python -m cProfile -o profile.stats pdr sim my_ppss.yaml
```

Then view profile results, w custom analysis:
```console
view_stats
```

## Dev: Dependencies
See [dependencies.md](dependencies.md).
