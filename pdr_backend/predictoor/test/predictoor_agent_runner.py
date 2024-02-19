"""
This file exposes run_agent_test()
which is used by test_predictoor_agent{1,3}.py
"""
import os
from unittest.mock import Mock

from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import mock_feed_ppss, mock_ppss
from pdr_backend.ppss.web3_pp import (
    inplace_mock_query_feed_contracts,
    inplace_mock_w3_and_contract_with_tracking,
)
from pdr_backend.subgraph.subgraph_feed import mock_feed

PRIV_KEY = os.getenv("PRIVATE_KEY")
OWNER_ADDR = "0xowner"
INIT_TIMESTAMP = 107
INIT_BLOCK_NUMBER = 13


@enforce_types
def get_agent_1feed(tmpdir: str, monkeypatch, predictoor_agent_class):
    """
    @description
      Initialize the agent, and return it along with related info
      For 1 feed (vs 2 or other).

    @return
      feed -- SubgraphFeed, eg for binance BTC/USDT 5m
      ppss -- PPSS
      agent -- PredictoorAgent{1,3,..}
      pdr_contract -- PredictoorContract corresponding to the feed
    """
    monkeypatch.setenv("PRIVATE_KEY", PRIV_KEY)
    feed, ppss = mock_feed_ppss(
        "5m", "binanceus", "BTC/USDT", network="development", tmpdir=tmpdir
    )
    inplace_mock_query_feed_contracts(ppss.web3_pp, feed)

    pdr_contract = inplace_mock_w3_and_contract_with_tracking(
        ppss.web3_pp,
        INIT_TIMESTAMP,
        INIT_BLOCK_NUMBER,
        ppss.predictoor_ss.timeframe_s,
        feed.address,
        monkeypatch,
    )

    # now we're done the mocking, time for the real work!!

    # real work: initialize
    agent = predictoor_agent_class(ppss)

    return (feed, ppss, agent, pdr_contract)


@enforce_types
def get_agent_2feeds(tmpdir: str, monkeypatch, predictoor_agent_class):
    """
    @description
      Initialize the agent, and return it along with related info
      For 2 feeds (vs 1 or other)

    @return
      feeds -- list of SubgraphFeed, eg for binance {BTC,ETH}/USDT 5m
      ppss -- PPSS
      agent -- PredictoorAgent{1,3,..}
    """
    monkeypatch.setenv("PRIVATE_KEY", PRIV_KEY)

    exchange, timescale, quote = "binanceus", "5m", "USDT"
    coins = ["BTC", "ETH"]
    feeds = [mock_feed(timescale, exchange, f"{c}/{quote}") for c in coins]
    ppss = mock_ppss(
        [f"{exchange} {c}/{quote} c {timescale}" for c in coins],
        network="development",
        tmpdir=tmpdir,
    )

    ppss.web3_pp.query_feed_contracts = Mock()
    ppss.web3_pp.query_feed_contracts.return_value = {
        feed.address: feed for feed in feeds
    }

    # mock w3
    ppss.web3_pp._web3_config = Mock()
    ppss.web3_pp._web3_config.w3 = Mock()
    ppss.web3_pp._web3_config.w3.eth = Mock()

    # mock pdr contract
    pdr_contract = Mock()
    contract_func = Mock()
    contract_func.return_value = pdr_contract
    monkeypatch.setattr(
        "pdr_backend.contract.predictoor_contract.PredictoorContract",
        contract_func,
    )

    # now we're done the mocking, time for the real work!!

    # real work: initialize
    agent = predictoor_agent_class(ppss)

    return (feeds, ppss, agent)


@enforce_types
def run_agent_test(tmpdir: str, monkeypatch, predictoor_agent_class):
    """
    @description
        Run the agent for a while, and then do some basic sanity checks.

        Uses get_agent_1feed (not 2feeds)
    """
    _, ppss, agent, _mock_pdr_contract = get_agent_1feed(
        tmpdir, monkeypatch, predictoor_agent_class
    )
    # now we're done the mocking, time for the real work!!

    # real work: main iterations
    for _ in range(500):
        agent.take_step()

    # log some final results for debubbing / inspection
    mock_w3 = ppss.web3_pp.web3_config.w3
    print("\n" + "/" * 160)
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
    assert (mock_w3.eth.timestamp + 2 * ppss.predictoor_ss.timeframe_s) >= max(
        _mock_pdr_contract._prediction_slots
    )
