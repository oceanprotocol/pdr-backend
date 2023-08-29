import csv
import os
import time
from typing import List

import ccxt
import numpy as np
import pandas as pd

from pdr_backend.predictoor.approach2.predict import get_prediction

@enforce_types
class PredictoorApproach2Config(PredictoorConfig):
    def __init__(self):
        super().__init()
                
        self.get_prediction = get_prediction # set prediction function

        # example: directory from git clone of oceanprotocol/pdr-model-simple
        model_dir: str = getenv_or_exit("MODELDIR")
        
        # OceanModel module lives in $MODELDIR/model.py
        sys.path.append(model_dir)
        from model import OceanModel  # type: ignore  # fmt: off # pylint: disable=wrong-import-order, wrong-import-position

        # pickled trained models live in $MODELDIR/trained_models/
        self.trained_models_dir = os.path.join(model_dir, "trained_models")

        # results csvs live in $self.results_dir/
        self.results_dir = "results"
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)


@enforce_types
class PredictoorApproach2:
    
    def __init__(self):
        super().__init()
        self.config = PredictoorApproach1Config()
        self.models = {} # [addr] : OceanModel
        self.feeds = {} # [addr] : feed, where feed is {"pair":..}
        self.exchanges = {} # [addr] : ccxt exchange
        self.dfs = {} # [addr] : DataFrame holding tohlcv data & predictions
        self.csv_names = {} # [addr] : str
        
        self.prev_block_time: int = 0
        self.prev_block_number: int = 0
        self.prev_submitted_epochs = {addr : 0 for addr in self._addrs()}
        
        self._initialize_models_and_feeds()
        self._initialize_exchanges()
        self._initialize_dfs()      
        self._initialize_csvs()     
        
    def run(self):
        print("Starting main loop...")
        while True:
            self.take_step()
    
    def take_step(self):
        # base data
        w3 = self.config.web3_config.w3
        
        # grab latest data
        self._update_dfs()

        # at new block number yet?
        block_number = w3.eth.block_number
        if block_number <= self.prev_block_number:
            time.sleep(1)
            return
        self.prev_block_number = block_number

        # is new block ready yet?
        block = w3.eth.get_block(block_number, full_transactions=False)
        if not block:
            return
        self.prev_block_time = block["timestamp"]
        print(f"Got new block, with number {block_number}")

        # do work at new block
        for addr in self._addrs():
            self._process_block_at_feed(addr, block["timestamp"])

    def _process_block_at_feed(self, addr: str, timestamp: str):
        # if new candle, process it
        model, df = self.models[addr], self.dfs[addr]

        predval = df.iloc[-2][model.model_name]
        have_predval = not np.isnan(predval)
        if have_predval:
            self._update_results_csv(addr)

        # get predictions
        index = df.index.values[-1]
        cur_predval = df.iloc[-1][model.model_name]
        have_cur_predval = not np.isnan(cur_predval)
        if not have_cur_predval:
            df.drop(columns_models + ["datetime"], axis=1),
            predval = self._log_loop(addr, block_number)
            if predval is not None:
                df.loc[index, [model.model_name]] = float(predval)

        # log
        cols_to_hide = ["volume", "open", "high", "low"]
        print(df.loc[:, ~df.columns.isin(cols_to_hide)].tail(15))

    def _initialize_models_and_feeds(self):
        """load models, whichever ones are available"""
        assert not self.models
        assert not self.feeds
        
        cand_feeds = self.config.get_feeds() # [addr] : feed
        for addr, feed in cand_feeds.items():
            exchange_id = feed["exchange_id"] # eg "binance"
            pair = feed["pair"]               # eg "BTC/USDT"
            timeframe = feed["timeframe"]     # eg "5m"
            
            model = OceanModel(exchange_id, pair, timeframe)
            try:
                model.unpickle_model(self.trained_models_dir)
            except:
                model = None
                
            if model is None:
                continue
            
            self.models[addr] = model
            self.feeds[addr] = feed

    def _initialize_csvs(self):
        assert self.feeds
        assert not self.csv_names
        
        # initialize csv_names
        ts_now = int(time.time())
        for addr in self._addrs():
            feed = self.feeds[addr]
            csv_name = \
                f"./{self.results_dir}/{feed['exchange_id']}_{feed['pair']}" \
                f"_{feed['timeframe']}_{ts_now}.csv"
            self.csv_names[addr] = csv_name

        # initialize csv files: write headers
        for addr in self._addrs():
            csv_name = self.csv_names[addr]
            if _csv_has_data(csv_name):
                continue
            with open(csv_name, "a") as f:
                writer = csv.writer(f)
                writer.writerow(self.df_cols)

    def _initialize_exchanges(self):
        assert self.feeds
        assert not self.exchanges
        
        for addr in self._addrs():
            feed = self.feeds[addr]
            exchange_class = getattr(ccxt, feed["exchange_id"])
            exchange = exchange_class({"timeout": 30000})
            self.exchanges[addr] = exchange

    def _initialize_dfs(self):
        assert self.models
        assert self.exchanges
        assert self.feeds
        assert self.exchanges
        assert not self.df_cols
        assert not self.dfs
        
        # initialize self.df_cols
        self.df_cols = \
            ["datetime", "open", "high", "low", "close", "volume"] + \
            self._models_cols() # prediction col. 0 or 1

        # fill in self.dfs with initial data
        for addr in self._addrs():
            feed, exchange = self.feeds[addr], self.exchanges[addr]
            self.dfs[addr] = pd.DataFrame(columns=self.df_cols)
            candles = self.exchange_ccxt.fetch_ohlcv(feed["pair"], "5m")
            for candle in candles:
                _update_df_at_candle(self.dfs[addr], candle)
    
    def _update_results_csv(self, addr: str):
        model, csv_name = self.models[addr], self.csv_names[addr]
        
        with open(csv_name, "a") as f:
            writer = csv.writer(f)
            row = [
                df.index.values[-2],
                df.iloc[-2]["datetime"],
                df.iloc[-2]["open"],
                df.iloc[-2]["high"],
                df.iloc[-2]["low"],
                df.iloc[-2]["close"],
                df.iloc[-2]["volume"],
            ]
            row.append(df.iloc[-2][model.model_name])
            writer.writerow(row)

    def _update_dfs(self):
        """Update self.dfs with the two most recent candles"""
        for addr in self._addrs():
            feed, df = self.feeds[addr], self.dfs[addr]
            candles = self.exchange_ccxt.fetch_ohlcv(feed["pair"], "5m")
            recent_candles = candles[-2:]
            for candle in recent_candles:
                _update_df_at_candle(df, candle)
    
    def _addrs(self) -> List[str]:
        """Return addresses in a deterministic order."""
        assert self.feeds
        return sorted(self.feeds.keys())
    
    def _models_cols(self) -> List[str]:
        return [self.models[addr].model_name for addr in self._addrs()]


@enforce_types
def _csv_has_data(filename: str) -> bool:
    size = 0
    try:
        files_stats = os.stat(results_csv_name)
        size = files_stats.st_size
    except:  # pylint: disable=bare-except
        pass

    return (size > 0)

@enforce_types
def _update_df_at_candle(df: DataFrame, candle: list):
    """Updates the df in-place with info from candle"""
    t,o,h,l,c,v = _tohlcv_tuple(candle)
    df.loc[t] =  _tohlcv_dict(t,o,h,l,c,v)                
    df.loc[t, ["datetime"]] = _to_datetime(t)

@enforce_types         
def _tohlcv_tuple(candle: list) -> tuple[int,float,float,float,float,float]:
    t = int(candle[0] / 100)
    o = float(candle[1])
    h = float(candle[2])
    l = float(candle[3])
    c = float(candle[4])
    v = float(candle[5])
    return t,o,h,l,c,v

@enforce_types
def _tohlcv_dict(t,o,h,l,c,v) -> dict:
    return {
        "timestamp": t,
        "open": o,
        "high": h,
        "low": l,
        "close": c,
        "volume": v,
    }

@enforce_types
def _to_datetime(ts):
    return pd.to_datetime(ts, unit="s", utc=True)

@enforce_types
def main():
    p = PredictoorApproach2()
    p.run()

if __name__ == "__main__":
    main()
