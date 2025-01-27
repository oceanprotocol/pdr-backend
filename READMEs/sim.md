# Run sim/trading

Predict, trade, make $. Historical, live mock, or live real. This README shows how.

Steps:
1. Install pdr-backend repo
2. Sim / mock trade, on historical data
3. Sim / mock trade, on live data 
4. Trade on live real data
5. Optimize


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

## Sim / mock trade, on historical data

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
1. Set simulation parameters.
2. Grab historical price data from exchanges and stores in `lake_data/` dir. It re-uses any previously saved data.
3. Run through many 5 min epochs. At each epoch:
   - Build a model or get predictions from chain
   - Predict
   - Trade
   - Log to console and `logs/out_<time>.txt`

By default, simulation uses a linear model inputting prices of the previous 2-10 epochs as inputs (autoregressive_n), just BTC close price as input, a simulated 0% trading fee, and a trading strategy of "buy if predict up; sell 5min later". You can play with different values in `my_ppss.yaml`.

Profit isn't guaranteed: fees, slippage and more eats into them. Model accuracy makes a big difference too.

To see simulation CLI options: `pdr sim -h`.

Simulation uses Python [logging](https://docs.python.org/3/howto/logging.html) framework. Configure it via [`logging.yaml`](../logging.yaml). [Here's](https://medium.com/@cyberdud3/a-step-by-step-guide-to-configuring-python-logging-with-yaml-files-914baea5a0e5) a tutorial on yaml settings.



## Sim / mock trade on live data

In my_ppss.yaml, set `tradetype` as `livemock`. This will simulate & mock-trade on _live_ data.

Let's run the engine! In console:
```console
pdr sim my_ppss.yaml
```


## Trade on real data


In my_ppss.yaml, set `tradetype` as `livereal`. This will trade _for real_ on _live_ data. 

Let's run the engine! In console:
```console
pdr sim my_ppss.yaml
```

Be careful, it's real $!


# Go beyond: Optimize

You've gone through all the essential steps to earn $ by running a trader bot on mainnet.

The next sections describe how to go beyond, by optimizing the trading strategy and more.

## Optimize Trading Strategy

Once you're familiar with the above, you can set your own trading strategy and optimize it for $. Here's how:

1. Fork `pdr-backend` repo.
1. Change sim / trading code as you wish, while iterating with `histmock` and `livemock` simulations.
1. Flip over to `livereal`, and trade for real


# Right-size trading

The default trader bot approaches have a fixed-amount trade with a small default value. Yet the more you trade, the more you can earn, up to a point: if you trade too much then you encounter slippage, and too much slippage will make you lose $.

So what's the right amount?

See Kelly Criterion. (FIXME)

## Warning

You will lose money trading if your $ out exceeds your $ in. Do account for trading fees, order book slippage, cost of prediction feeds, and more. Everything you do is your responsibility, at your discretion. None of this repo is financial advice.

