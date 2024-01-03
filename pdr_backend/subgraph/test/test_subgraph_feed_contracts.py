import pytest
import requests
from enforce_typing import enforce_types

from pdr_backend.cli.timeframe import Timeframe
from pdr_backend.subgraph.info725 import info_to_info725
from pdr_backend.subgraph.subgraph_feed import SubgraphFeed
from pdr_backend.subgraph.subgraph_feed_contracts import query_feed_contracts
from pdr_backend.subgraph.test.resources import MockPost


@enforce_types
def mock_contract(info: dict, symbol: str) -> dict:
    info725 = info_to_info725(info)

    contract = {
        "id": "0xNFT1",
        "token": {
            "id": "0xDT1",
            "name": f"Name:{symbol}",
            "symbol": symbol,
            "nft": {
                "owner": {
                    "id": "0xowner1",
                },
                "nftData": info725,
            },
        },
        "secondsPerEpoch": Timeframe(info["timeframe"]).s,
        "secondsPerSubscription": 700,
        "truevalSubmitTimeout": 5,
    }
    return contract


@enforce_types
def test_query_feed_contracts__emptychain(monkeypatch):
    contract_list = []
    monkeypatch.setattr(requests, "post", MockPost(contract_list))
    contracts = query_feed_contracts(subgraph_url="foo")
    assert contracts == {}


@enforce_types
def test_query_feed_contracts__fullchain(monkeypatch):
    # This test is a simple-as-possible happy path. Start here.
    # Then follow up with test_filter() below, which is complex but thorough

    info = {"pair": "BTC/USDT", "timeframe": "5m", "source": "binance"}
    contract = mock_contract(info, "contract1")
    contract_addr = contract["id"]

    contract_list = [contract]
    monkeypatch.setattr(requests, "post", MockPost(contract_list))

    feeds = query_feed_contracts(subgraph_url="foo")

    assert len(feeds) == 1
    assert contract_addr in feeds
    feed = feeds[contract_addr]
    assert isinstance(feed, SubgraphFeed)

    assert feed.name == "Name:contract1"
    assert feed.address == "0xNFT1"
    assert feed.symbol == "contract1"
    assert feed.seconds_per_subscription == 700
    assert feed.trueval_submit_timeout == 5
    assert feed.owner == "0xowner1"
    assert feed.pair == "BTC/USDT"
    assert feed.timeframe == "5m"
    assert feed.source == "binance"
    assert feed.seconds_per_epoch == 5 * 60


@enforce_types
@pytest.mark.parametrize(
    "expect_result, owners",
    [
        (True, None),
        (True, ""),
        (True, "0xowner1"),
        (False, "0xowner2"),
        (True, "0xowner1,0xowner2"),
        (False, "0xowner2,0xowner3"),
    ],
)
def test_query_feed_contracts__filter(monkeypatch, expect_result, owners):
    info = {"pair": "BTC/USDT", "timeframe": "5m", "source": "binance"}
    info725 = info_to_info725(info)

    contract1 = {
        "id": "contract1",
        "token": {
            "id": "token1",
            "name": "ether",
            "symbol": "ETH",
            "nft": {
                "owner": {
                    "id": "0xowner1",
                },
                "nftData": info725,
            },
        },
        "secondsPerEpoch": 7,
        "secondsPerSubscription": 700,
        "truevalSubmitTimeout": 5,
    }
    contract_list = [contract1]

    monkeypatch.setattr(requests, "post", MockPost(contract_list))
    feed_dicts = query_feed_contracts("foo", owners)

    assert bool(feed_dicts) == bool(expect_result)
