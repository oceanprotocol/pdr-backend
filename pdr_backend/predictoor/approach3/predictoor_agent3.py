import os
from typing import Tuple

from enforce_typing import enforce_types
from pdr_backend.simulation.data_factory import DataFactory
from pdr_backend.simulation.model_factory import ModelFactory
from pdr_backend.simulation.model_ss import ModelSS

from pdr_backend.predictoor.base_predictoor_agent import BasePredictoorAgent
from pdr_backend.predictoor.approach3.predictoor_config3 import PredictoorConfig3
from pdr_backend.simulation.timeutil import timestr_to_ut
from pdr_backend.simulation.data_ss import DataSS

import time
from datetime import datetime

import asyncio

@enforce_types
class PredictoorAgent3(BasePredictoorAgent):
    predictoor_config_class = PredictoorConfig3

    def __init__(self, config: PredictoorConfig3):
        super().__init__(config)
        self.config: PredictoorConfig3 = config

    def run(self):
        print("Starting main loop...")
        while True:
            asyncio.run(self._take_step())

    async def _take_step(self):
        w3 = self.config.web3_config.w3
        print("\n" + "-" * 80)
        print("Take_step() begin.")

        # new block?
        block_number = w3.eth.block_number
        print(f"  block_number={block_number}, prev={self.prev_block_number}")
        if block_number <= self.prev_block_number:
            print("  Done step: block_number hasn't advanced yet. So sleep.")
            time.sleep(1)
            return
        block = self.config.web3_config.get_block(block_number, full_transactions=False)
        if not block:
            print("  Done step: block not ready yet")
            return
        self.prev_block_number = block_number
        self.prev_block_timestamp = block["timestamp"]

        # do work at new block
        print(f"  Got new block. Timestamp={block['timestamp']}")
        tasks = [
            self._async_process_block_at_feed(addr, block["timestamp"]) for addr in self.feeds
        ]
        predval, stake, success = zip(*await asyncio.gather(*tasks))

        print("  Done step: success.")
        print(f"  predval={predval}, stake={stake}, success={success}")

    def get_prediction(
        self, addr: str, timestamp: int  # pylint: disable=unused-argument
    ) -> Tuple[bool, float]:
        """
        @description
          Given a feed, let's predict for a given timestamp.

        @arguments
          addr -- str -- address of the trading pair. Info in self.feeds[addr]
          timestamp -- int -- when to make prediction for (unix time)

        @return
          predval -- bool -- if True, it's predicting 'up'. If False, 'down'
          stake -- int -- amount to stake, in units of Eth
        """
        # Set model_ss
        model_ss = ModelSS(
            self.config.model_ss
        )  # PREV, LIN, GPR, SVR, NuSVR, LinearSVR

        # Controllable data_ss params. Hardcoded; could be moved to envvars

        coins = ["ETH", "BTC"]
        signals = self.config.signals
        exchange_ids = self.config.exchange_ids

        # Uncontrollable data_ss params
        feed = self.feeds[addr]
        timeframe = feed.timeframe  # eg 5m, 1h
        yval_coin = feed.base  # eg ETH
        usdcoin = feed.quote  # eg USDT
        yval_exchange_id = feed.source
        yval_signal = "close"

        if yval_coin not in coins:  # eg DOT
            coins.append(yval_coin)
        if yval_exchange_id not in exchange_ids:
            exchange_ids.append(yval_exchange_id)

        # Set data_ss
        data_ss = DataSS(
            csv_dir=os.path.abspath("csvs"),
            st_timestamp=self.config.st_timestamp,
            fin_timestamp=timestr_to_ut("now"),
            max_N_train=self.config.max_N_train,
            N_test=self.config.N_test,
            Nt=self.config.Nt,
            usdcoin=usdcoin,
            timeframe=timeframe,
            signals=signals,
            coins=coins,
            exchange_ids=exchange_ids,
            yval_exchange_id=yval_exchange_id,
            yval_coin=yval_coin,
            yval_signal=yval_signal,
        )

        data_factory = DataFactory(data_ss)

        # Compute X/y
        hist_df = data_factory.get_hist_df()
        X, y, _, _ = data_factory.create_xy(hist_df, testshift=0)

        # Split X/y
        st, fin = 0, X.shape[0] - 1
        X_train, X_test = X[st:fin, :], X[fin : fin + 1]
        y_train, _ = y[st:fin], y[fin : fin + 1]

        # Compute the model
        model_factory = ModelFactory(model_ss)
        model = model_factory.build(X_train, y_train)

        # Predict
        predprice = model.predict(X_test)[0]
        curprice = y_train[-1]
        predval = predprice > curprice

        # Stake what was set via envvar STAKE_AMOUNT
        stake = self.config.stake_amount

        return (bool(predval), stake)

    async def _async_process_block_at_feed(self, addr: str, timestamp: int) -> tuple:
        """Returns (predval, stake, submitted)"""
        # base data
        feed, contract = self.feeds[addr], self.contracts[addr]
        epoch = contract.get_current_epoch()
        s_per_epoch = feed.seconds_per_epoch
        
        # we want to subtract from now rather than last_block timestamp so we can account for run time between feeds this agent is serving
        epoch_s_left = epoch * s_per_epoch + s_per_epoch - datetime.now().timestamp()

        # print status
        print(f"    Process {feed} at epoch={epoch}")

        # within the time window to predict?
        print(
            f"      {epoch_s_left} s left in epoch"
            f" (predict if <= {self.config.s_until_epoch_end} s left)"
        )
        too_early = epoch_s_left > self.config.s_until_epoch_end
        if too_early:
            print("      Done feed: too early to predict")
            return (None, None, False)

        # compute prediction; exit if no good
        target_time = (epoch + 2) * s_per_epoch
        print(f"      Predict for time slot = {target_time}...")

        predval, stake = self.get_prediction(addr, target_time)
        print(f"      -> Predict result: predval={predval}, stake={stake}")
        if predval is None or stake <= 0:
            print("      Done feed: can't use predval/stake")
            return (None, None, False)

        # submit prediction to chain
        print("      Submit predict tx chain...")
        contract.submit_prediction(predval, stake, target_time, True)
        self.prev_submit_epochs_per_feed[addr].append(epoch)
        print("      " + "=" * 80)
        print("      -> Submit predict tx result: success.")
        print("      " + "=" * 80)
        print("      Done feed: success.")
        return (predval, stake, True)