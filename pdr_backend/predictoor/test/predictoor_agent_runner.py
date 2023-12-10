"""
This file exposes run_agent_test()
which is used by test_predictoor_agent{1,3}.py
"""
import os

from enforce_typing import enforce_types

from pdr_backend.ppss.data_pp import DataPP
from pdr_backend.ppss.data_ss import DataSS
from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str, mock_feed_ppss
from pdr_backend.ppss.web3_pp import (
    inplace_mock_query_feed_contracts,
    inplace_mock_w3_and_contract_with_tracking,
)

PRIV_KEY = os.getenv("PRIVATE_KEY")
OWNER_ADDR = "0xowner"
INIT_TIMESTAMP = 107
INIT_BLOCK_NUMBER = 13


@enforce_types
def run_agent_test(tmpdir, monkeypatch, predictoor_agent_class):
    monkeypatch.setenv("PRIVATE_KEY", PRIV_KEY)
    feed, ppss = mock_feed_ppss("5m", "binanceus", "BTC/USDT", tmpdir=tmpdir)
    inplace_mock_query_feed_contracts(ppss.web3_pp, feed)

    _mock_pdr_contract = inplace_mock_w3_and_contract_with_tracking(
        ppss.web3_pp,
        INIT_TIMESTAMP,
        INIT_BLOCK_NUMBER,
        ppss.data_pp.timeframe_s,
        feed.address,
        monkeypatch,
    )

    # now we're done the mocking, time for the real work!!

    # real work: initialize
    agent = predictoor_agent_class(ppss)

    # real work: main iterations
    for _ in range(100):
        agent.take_step()

    # log some final results for debubbing / inspection
    mock_w3 = ppss.web3_pp.web3_config.w3
    print("\n" + "=" * 80)
    print("Done iterations")
    print(
        f"init block_number = {INIT_BLOCK_NUMBER}"
        f", final = {mock_w3.eth.block_number}"
    )
    print()
    print(f"init timestamp = {INIT_TIMESTAMP}, final = {mock_w3.eth.timestamp}")
    print(f"all timestamps seen = {mock_w3.eth._timestamps_seen}")
    print()
    print(
        "unique prediction_slots = "
        f"{sorted(set(_mock_pdr_contract._prediction_slots))}"
    )
    print(f"all prediction_slots = {_mock_pdr_contract._prediction_slots}")

    # relatively basic sanity tests
    assert _mock_pdr_contract._prediction_slots
    assert (mock_w3.eth.timestamp + 2 * ppss.data_pp.timeframe_s) >= max(
        _mock_pdr_contract._prediction_slots
    )


@enforce_types
def _ppss(tmpdir) -> PPSS:
    yaml_str = fast_test_yaml_str(tmpdir)
    ppss = PPSS(yaml_str=yaml_str, network="development")

    assert hasattr(ppss, "data_pp")
    ppss.data_pp = DataPP(
        {
            "timeframe": "5m",
            "predict_feeds": ["binanceus c BTC/USDT"],
            "sim_only": {"test_n": 10},
        }
    )
    assert hasattr(ppss, "data_ss")
    ppss.data_ss = DataSS(
        {
            "input_feeds": ["binanceus c BTC/USDT"],
            "parquet_dir": os.path.join("parquet_data"),
            "st_timestr": "2023-06-18",
            "fin_timestr": "2023-07-21",
            "max_n_train": 100,
            "autoregressive_n": 2,
        }
    )

    return ppss
