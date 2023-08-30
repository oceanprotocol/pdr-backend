import csv
import os
from os import getenv
import sys
import time
from typing import List

import ccxt
import numpy as np
import pandas as pd

from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.predictoor.approach2.predict import predict_function
from pdr_backend.util.env import getenv_or_exit
from pdr_backend.util.subgraph import query_predictContracts
from pdr_backend.util.web3_config import Web3Config

# set envvar model MODELDIR before calling main.py. eg ~/code/pdr-model-simple/
# then, the pickled trained models live in $MODELDIR/trained_models/
# and, OceanModel module lives in $MODELDIR/model.py
model_dir: str = getenv_or_exit("MODELDIR")
trained_models_dir = os.path.join(model_dir, "trained_models")
sys.path.append(model_dir)
from model import OceanModel  # type: ignore  # fmt: off # pylint: disable=wrong-import-order, wrong-import-position

rpc_url = getenv_or_exit("RPC_URL")
subgraph_url = getenv_or_exit("SUBGRAPH_URL")
private_key = getenv_or_exit("PRIVATE_KEY")
pair_filters = getenv("PAIR_FILTER")
timeframe_filter = getenv("TIMEFRAME_FILTER")
source_filter = getenv("SOURCE_FILTER")
owner_addresses = getenv("OWNER_ADDRS")

exchange_id = "binance"
pair = "BTC/USDT"
timeframe = "5m"

# ===================
# done imports and constants. Now start running...

prev_block_time = 0
feeds: List[dict] = []

exchange_class = getattr(ccxt, exchange_id)
exchange_ccxt = exchange_class({"timeout": 30000})

web3_config = Web3Config(rpc_url, private_key)
owner = web3_config.owner

models = [
    OceanModel(exchange_id, pair, timeframe),
]


def main():  # pylint: disable=too-many-statements
    print("Starting main loop...")

    results_dir = "results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    ts_now = int(time.time())
    csv_name = (f"./{results_dir}/{exchange_id}_{models[0].pair}"
                f"_{models[0].timeframe]}_{ts_now}.csv")

    all_columns = []
    for model in models:
        model.unpickle_model(trained_models_dir)
        pred_col = model.model_name
        all_columns.append(pred_col) # prediction column.  0 or 1

    # write csv header for results
    if not _csv_has_data(csv_name):
        with open(csv_name, "a") as f:
            writer = csv.writer(f)
            writer.writerow(all_columns)

    # read initial set of candles
    candles = exchange_ccxt.fetch_ohlcv(pair, "5m")
    # load past data
    df = pd.DataFrame(columns=all_columns)
    for ohl in candles:
        ohlc = {
            "timestamp": int(ohl[0] / 1000),
            "open": float(ohl[1]),
            "close": float(ohl[4]),
            "low": float(ohl[3]),
            "high": float(ohl[2]),
            "volume": float(ohl[5]),
        }
        df.loc[ohlc["timestamp"]] = ohlc
        df["datetime"] = pd.to_datetime(df.index.values, unit="s", utc=True)

    lastblock = 0
    prev_finalized_timestamp = 0
    while True:
        candles = exchange_ccxt.fetch_ohlcv(pair, "5m")
        recent_candles = candles[-2:]
        for candle in recent_candles:
            _update_df_at_candle(df, candle)

        timestamp = df.index.values[-2]

        block = web3_config.w3.eth.block_number
        if block <= lastblock:
            time.sleep(1)
            continue
        
        lastblock = block

        # #we have a new candle
        if prev_finalized_timestamp < timestamp:
            prev_finalized_timestamp = timestamp

            should_write = False
            for model in models:
                predval = df.iloc[-2][model.model_name]
                if not np.isnan(predval):
                    should_write = True

            if should_write:
                pred_cols = [model.model_name for model in models]
                row = _row_for_csv(df, -2, pred_cols)
                _add_row_to_csv(row, csv_name)

        for model in models:
            index = df.index.values[-1]
            cur_predval = df.iloc[-1][model.model_name]
            if not np.isnan(cur_predval):
                continue

            block = web3_config.w3.eth.get_block(blockno, full_transactions=False)
            if not block:
                continue
            
            df_for_model = df.drop(columns_models + ["datetime"], axis=1)
            global prev_block_time
            prev_block_time = block["timestamp"]
            predval = process_block(block, model, df_for_model)
            if predval is None:
                continue
            
            df.loc[index, [model.model_name]] = float(predval)

        print(
            df.loc[
                :, ~df.columns.isin(["volume", "open", "high", "low"])
            ].tail(15)
        )



def process_block(block, model, df):
    """
    Process each contract.
    If needed, get a prediction, submit it and claim revenue for past epoch
    """
    global feeds
    if not feeds:
        feeds = query_predictContracts(
            subgraph_url,
            pair_filters,
            timeframe_filter,
            source_filter,
            owner_addresses,
        )

    print(f"Got new block: {block['number']} with {len(feeds)} feeds")

    for address in feeds:
        feed = feeds[address]
        predictoor_contract = PredictoorContract(web3_config, address)
        epoch = predictoor_contract.get_current_epoch()
        seconds_per_epoch = predictoor_contract.get_secondsPerEpoch()
        seconds_till_epoch_end = (
            epoch * seconds_per_epoch + seconds_per_epoch - block["timestamp"]
        )
        print(
            f"\t{feed['name']} (at address {feed['address']} is at "
            f"epoch {epoch}, seconds_per_epoch: {seconds_per_epoch}"
            f", seconds_till_epoch_end: {seconds_till_epoch_end}"
        )

        if epoch > feed["prev_submited_epoch"] and feed["prev_submited_epoch"] > 0:
            # let's get the payout for previous epoch.  We don't care if it fails...
            slot = epoch * seconds_per_epoch - seconds_per_epoch
            print(
                f"Contract:{predictoor_contract.contract_address} - "
                f"Claiming revenue for slot:{slot}"
            )
            predictoor_contract.payout(slot, False)

        if seconds_till_epoch_end <= int(getenv("SECONDS_TILL_EPOCH_END", "60")):
            # Timestamp of prediction
            target_time = (epoch + 2) * seconds_per_epoch

            # Fetch the prediction
            (predicted_value, predicted_confidence) = predict_function(
                feed, target_time, model, df
            )

            if predicted_value is not None and predicted_confidence > 0:
                # We have a prediction, let's submit it
                stake_amount = (
                    int(getenv("STAKE_AMOUNT", "1")) * predicted_confidence / 100
                )  # TO DO have a customizable function to handle this
                print(
                    f"Contract:{predictoor_contract.contract_address} - "
                    f"Submitting prediction for slot:{target_time}"
                )
                predictoor_contract.submit_prediction(
                    predicted_value, stake_amount, target_time, True
                )
                feeds[address]["prev_submited_epoch"] = epoch
                return predicted_value

            print(
                "We do not submit, prediction function returned "
                f"({predicted_value}, {predicted_confidence})"
            )
    return None


@enforce_types
def _row_for_csv(df, row_index, pred_cols) -> list:
    row = [
        df.index.values[row_index],
        df.iloc[row_index]["datetime"],
        df.iloc[row_index]["open"],
        df.iloc[row_index]["high"],
        df.iloc[row_index]["low"],
        df.iloc[row_index]["close"],
        df.iloc[row_index]["volume"],
    ]
    for pred_col in pred_cols:
        row.append(df.iloc[row_index][pred_col])
    
@enforce_types
def _add_row_to_csv(row:list, csv_name:str):        
    with open(csv_name, "a") as f:
        writer = csv.writer(f)
        writer.writerow(row)

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
