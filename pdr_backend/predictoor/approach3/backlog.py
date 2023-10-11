
#TODOs Backlog: GOAL = $$$

# - in play.py, it currently prints a "time" but that's not necessarily the *correct* time. Fix it.
# - put it live, able to flip a switch to make real $

# - what happens when predictoor goes live? Then predictions will become a function of past predictions + buy/sell actions by predictoor agent.

# - handle bad exchange data: missing timestamps. data_factory.py mn/mx/diffs shows where
# - handle bad exchange data: screwball prices like 0.001 for 2017-09-01
# - handle bad exchange data: plot pdf of all prices and observe outliers

# - fancier trading: have full "triple barrier method" via (a) sell when price > max_threshold, ie "take profit" (b) sell when price < min_threshold, ie "stop loss". To do this, need to implement live tracking of price, how to do that

# -use order book in modeling: model inputs order book params
# -use order book in trading: keep simple trading algo, just model effects
# -fancier trading: choose how much to order based on order book info
# -fancier trading: on "down" predictions, short

# -to overcome shallow order book: use synthetic assets (via Synthetix) which have infinite depth (!!)
# -to choose right-size bet (based on confidence), use Kelly Criterion. https://en.wikipedia.org/wiki/Kelly_criterion. (May not affect us if order book shallowness constrains first. Though for deep order books via synthetics..)


# - don't just buy if "predprice>curprice", also account for tx fee of buy+sell

# - I currently have an AR model. Move to ARMA, then ARIMA. eg see https://towardsdatascience.com/time-series-models-d9266f8ac7b0
# - all: scale (bias) X, y to mean=0, stddev=1. See my original FFX.py
# - In X_train, weight newest sample eg 10 times. (And youngest n samples)
# - And lin model on Bin,ETH,kraken,Nt=2 should have a great 2-point fit

# - use signals from decentralized options markets like buffer. First, understand better!
# - refactor: use pandas "shift()" functionality instead of my custom "timeblock" module https://machinelearningmastery.com/convert-time-series-supervised-learning-problem-python/
# - leverage ta library. Has weighted average, more. https://technical-analysis-library-in-python.readthedocs.io/en/latest/
# - add feature vectors:
#   - Add feature vectors: H-L, H/L (=% change)
# - draw on Advances in Financial ML. https://www.amazon.com/Advances-Financial-Machine-Learning-Marcos/dp/1119482089
# - tune models better:
#   - LIN: try different lin modeling approaches (ridge, lasso)
#   - GPR: it's currently doing terrible, find out whey. Fix it. Then, try different kernels & params. Loop
#   - SVMs: apply "kernel approximation" tricks to scale WAY better: https://scikit-learn.org/stable/modules/kernel_approximation.html#polynomial-kernel-approximation-via-tensor-sketch
#   - SVMs: loop across different kernels & params
#   - FFX: copy & paste original FFX algo. Or write new version (safer). Tune it myself
#   - try my latent-variable projection trick (GPTP the year before FFX)
#   - try random-projection GPM
# - get more data. **Main aim: understand (a)(b)**:
#   **(a) where the big volumes for ETH are, then model prob(change) per block**
#   **(b) who the big holders of ETH are, then model prob(change) per block***
#   - add _all_ exchanges that collectively cover 99% of ETH volume
#      - therefore we add various CEXes & DEXes/chains. Uniswap, etc
#      - and also coins & volumes for intermediate. Eg BTC -> USDT -> ETH
#   - add higher-fidelity near-term data
#     - CEX orderbook data
#     - DEX-equivalents of orderbook data & more. Eg add/remove liq to pools
#     - ETH stake/unstake. Eg Lido
#     - ETH lock/unlock via loans & stablecoin. Eg DAI, Aave
#     - mempool data: bloxroute
#     - more coins
#   - get chain <> chain bridge data
#   - get chain <> CEX data by checking vol on known exchange accounts
# - more CEX data
#   - go farther back in time than 500 points. Alchemy? Other? Why: find holders
#   - add for ETH, but maybe not other coins (too much info)
# - try: predicting a coin with smaller marketcap. Why: fewer moving parts,
#   therefore more feasible to capture the majority of effects. OCEAN?
# - Add TokenSPICE trick:
#   - Use ganache to grab most recent data in eth mainnet & other. 
#   - Get it into tokenspice
#   - Populate  in tokenspice: AMMs, loans, bridges with top volume & liquidity
#   - Run tokenspice 1 block ahead
# - create trad'l prediction markets for price, take signals from them as inputs
# - create various synthetics around price, take signals from them as inputs

