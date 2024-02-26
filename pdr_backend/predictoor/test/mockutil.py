import os
from unittest.mock import Mock

from enforce_typing import enforce_types
import pytest

from pdr_backend.ppss.ppss import mock_feed_ppss, mock_ppss
from pdr_backend.ppss.web3_pp import (
    inplace_mock_query_feed_contracts,
    inplace_mock_w3_and_contract_with_tracking,
)
from pdr_backend.subgraph.subgraph_feed import mock_feed
from pdr_backend.util.time_types import UnixTimeS

PRIV_KEY = os.getenv("PRIVATE_KEY")
OWNER_ADDR = "0xowner"
INIT_TIMESTAMP = UnixTimeS(107)
INIT_BLOCK_NUMBER = 13


@enforce_types
def mock_ppss_1feed(approach: int, tmpdir: str, monkeypatch):
    """
    @description
      Initialize the agent, and return it along with related info
      For 1 feed (vs 2 or other).

    @return
      feed -- SubgraphFeed, eg for binance BTC/USDT 5m
      ppss -- PPSS
      pdr_contract -- PredictoorContract corresponding to the feed
    """
    # mock ppss, feed
    monkeypatch.setenv("PRIVATE_KEY", PRIV_KEY)
    feed, ppss = mock_feed_ppss(
        "5m", "binanceus", "BTC/USDT", network="development", tmpdir=tmpdir
    )
    ppss.predictoor_ss.set_approach(approach)

    # mock ppss.web3_pp.query_feed_contracts()
    inplace_mock_query_feed_contracts(ppss.web3_pp, feed)

    # mock w3, pdr contract
    pdr_contract = inplace_mock_w3_and_contract_with_tracking(
        ppss.web3_pp,
        INIT_TIMESTAMP,
        INIT_BLOCK_NUMBER,
        ppss.predictoor_ss.timeframe_s,
        feed.address,
        monkeypatch,
    )

    return (feed, ppss, pdr_contract)


@enforce_types
def mock_ppss_2feeds(approach: int, tmpdir: str, monkeypatch):
    """
    @description
      Initialize the agent, and return it along with related info
      For 2 feeds (vs 1 or other)

    @return
      feeds -- list of SubgraphFeed, eg for binance {BTC,ETH}/USDT 5m
      ppss -- PPSS
    """
    monkeypatch.setenv("PRIVATE_KEY", PRIV_KEY)

    # mock ppss, feeds
    exchange, timescale, quote = "binanceus", "5m", "USDT"
    coins = ["BTC", "ETH"]
    feeds: List[SubgraphFeed] = [
        mock_feed(timescale, exchange, f"{c}/{quote}") for c in coins
    ]
    ppss = mock_ppss(
        [f"{exchange} {c}/{quote} c {timescale}" for c in coins],
        network="development",
        tmpdir=tmpdir,
    )
    ppss.predictoor_ss.set_approach(approach)

    # mock ppss.web3_pp.query_feed_contracts()
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

    return (feeds, ppss)
