# Run a Trader Bot

This README takes shows how to earn $ by running a trader bot on mainnet, and beyond.

1. **[Install](#install-pdr-backend-repo)**
1. **[Simulate modeling & trading](#simulate-modeling-and-trading)**
1. **[Run bot on testnet](#run-trader-bot-on-sapphire-testnet)**
1. **[Run bot on mainnet](#run-trader-bot-on-sapphire-mainnet)**

Then, you can [go beyond](#go-beyond): [optimize trading strategy](#optimize-trading-strategy), and more.

## Install pdr-backend Repo

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

You need a local copy of Ocean contract addresses [`address.json`](https://github.com/oceanprotocol/contracts/blob/main/addresses/address.json). In console:
```console
# make directory if needed
mkdir -p ~/.ocean; mkdir -p ~/.ocean/ocean-contracts; mkdir -p ~/.ocean/ocean-contracts/artifacts/

# copy from github to local directory. Or, use wget if Linux. Or, download via browser.
curl https://github.com/oceanprotocol/contracts/blob/main/addresses/address.json -o ~/.ocean/ocean-contracts/artifacts/address.json
```

If you're running MacOS, then in console:

```console
# so that sapphire.py works. Details in #66
codesign --force --deep --sign - venv/sapphirepy_bin/sapphirewrapper-arm64.dylib

# so that xgboost works. Details in #1339
brew install libomp
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
2. Grab historical price data from exchanges and stores in `lake_data/` dir. It re-uses any previously saved data.
3. Run through many 5 min epochs. At each epoch:
   - Build a model or get predictions from chain
   - Predict
   - Trade
   - Log to console and `logs/out_<time>.txt`
   - For plots, output state to `sim_state/`

Let's visualize results. Open a separate console, and:
```console
cd ~/code/pdr-backend # or wherever your pdr-backend dir is
source venv/bin/activate
export PATH=$PATH:.

#start the plots server
pdr sim_plots
```

The plots server will give a url, such as [http://127.0.0.1:8050](http://127.0.0.1:8050). Open that url in your browser to see plots update in real time.

By default, simulation uses a linear model inputting prices of the previous 2-10 epochs as inputs (autoregressive_n), just BTC close price as input, a simulated 0% trading fee, and a trading strategy of "buy if predict up; sell 5min later". You can play with different values in `my_ppss.yaml`.

Profit isn't guaranteed: fees, slippage and more eats into them. Model accuracy makes a big difference too.

To see simulation CLI options: `pdr sim -h`.

Simulation uses Python [logging](https://docs.python.org/3/howto/logging.html) framework. Configure it via [`logging.yaml`](../logging.yaml). [Here's](https://medium.com/@cyberdud3/a-step-by-step-guide-to-configuring-python-logging-with-yaml-files-914baea5a0e5) a tutorial on yaml settings.

By default, Dash plots the latest sim (even if it is still running). To enable plotting for a specific run, e.g. if you used multisim or manually triggered different simulations, the sim engine assigns unique ids to each run.
Select that unique id from the `sim_state` folder, and run `pdr sim_plots --run_id <unique_id>` e.g. `pdr sim_plots --run_id 97f9633c-a78c-4865-9cc6-b5152c9500a3`

You can run many instances of Dash at once, with different URLs. To run on different ports, use the `--port` argument.

## Run Trader Bot in Mock Mode (livemock)

Predictoor contracts run on [Oasis Sapphire](https://docs.oasis.io/dapp/sapphire/) testnet and mainnet. Sapphire is a privacy-preserving EVM-compatible L1 chain.

Let's get our bot running on testnet first.

Then, copy & paste your private key as an envvar. In console:

```console
export PRIVATE_KEY=<YOUR_PRIVATE_KEY>
```

Then, run a simple trading bot. In console:

```console
pdr trader 2 my_ppss.yaml livemock (FIXME)
```

Your bot is running, congrats! Sit back and watch it in action.

It logs to console, and to `logs/out_<time>.txt`. Like simulation, it uses Python logging framework, configurable in `logging.yaml`.

To see trader CLI options: `pdr trader -h`

You can track behavior at finer resolution by writing more logs to the [code](../pdr_backend/trader/trader_agent.py)

## Run Trader Bot For Reals (livereal)

Then, copy & paste your private key as an envvar. (You can skip this if it's same as testnet.) In console:

```console
export PRIVATE_KEY=<YOUR_PRIVATE_KEY>
```

Update `my_ppss.yaml` as desired.

Then, run the bot. In console:

```console
pdr trader 2 my_ppss.yaml livereal (FIXME)
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


## Source of predictions

Choose the source of the predictions used as signals for trading:
- Use the builtin model. `use_own_model=True`
- Get the predictions from live feeds. `use_own_model=False`

By default `use_own_model` is set to `True`, and can be changed inside `my_ppss.yaml` file.


## Run Bots Remotely

To scale up compute or run without tying up your local machine, you can run bots remotely. Get started [here](remotebot.md).


## Optimize model: Tuning
Top-level tuning flow:
1. Use `multisim` tool to find optimal parameters, via simulation runs
1. Bring your model as a Trader bot to livemock then livereal

**Detailed tuning flow.** First, specify your sweep parameters & respective values in `my_ppss.yaml`, section `multisim_ss`. Here's an example.
```yaml
multisim_ss:
  approach: SimpleSweep # SimpleSweep | FastSweep (future) | ..
  sweep_params:
  - trader_ss.buy_amt: 1000 USD, 2000 USD
  - predictoor_ss.aimodel_ss.max_n_train: 500, 1000, 1500
  - predictoor_ss.aimodel_ss.input_feeds:
    -
      - binance BTC/USDT c 5m
    -
      - binance BTC/USDT ETH/USDT c 5m
      - kraken BTC/USDT c 5m
```

In the example, three parameters are being swept:
1. `trader_ss.buy_amt`, with two possible values: (i) `1000 USD` or (ii) `2000 USD`
1. `predictoor_ss.aimodel_ss.max_n_train`, with three possible values: (i) `500`, (ii) `1000`, or (iii) `1500`
1. `predictoor_ss.aimodel_ss.input_feeds`, with two possible values: (i) just binance BTC/USDT close price, or (ii) binance BTC/USDT & ETH/USDT close price, and kraken BTC/USDT close price.

The total number of combinations is 2 x 3 x 2 = 12.

Then, run `pdr multisim PPSS_FILE`.

The multisim tool will run a separate simulation for each of the 12 combinations.

As it runs, it will update a csv file summarizing results, as follows.
- name is `multisim_metrics_UNIX-TIME-MS.csv`, where UNIX-TIME-MS is the unix time at the start of the multisim run, in milliseconds.
- The columns of the csv are: run_number, performance metric 1, performance metric 2, ..., ppss setup parameter 1, setup parameter 2, ... .
  - Performance metrics are currently: "acc_est" (model prediction accuracy at end), "acc_l" (lower-bound accuracy), "acc_u" (upper-bound accuracy), "f1", "precision", "recall".
- The first row of the csv is the header. Each subsequent row is the results for a given run. For the example above, there will be 1+12 rows.

**Go further: write code.** You can go beyond tuning parameters, by developing your own data or modeling. Here's how:
1. Fork `pdr-backend` repo.
1. Change code for data, modeling, or otherwise as you wish. Run multisim to tune further
1. Bring your model as a Trader bot to livemock then livereal

# Right-size trading

The default trader bot approaches have a fixed-amount trade with a small default value. Yet the more you trade, the more you can earn, up to a point: if you trade too much then you encounter slippage, and too much slippage will make you lose $.

So what's the right amount?

See Kelly Criterion. (FIXME)

## Warning

You will lose money trading if your $ out exceeds your $ in. Do account for trading fees, order book slippage, cost of prediction feeds, and more. Everything you do is your responsibility, at your discretion. None of this repo is financial advice.

