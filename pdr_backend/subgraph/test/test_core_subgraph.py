from unittest.mock import patch

from enforce_typing import enforce_types
import pytest
import requests
from web3 import Web3
from pytest import approx

from pdr_backend.models.feed import Feed
from pdr_backend.models.slot import Slot
from pdr_backend.subgraph.core_subgraph import (
    block_number_is_synced,
    key_to_key725,
    value_to_value725,
    value725_to_value,
    info_to_info725,
    info725_to_info,
    query_subgraph,
    query_feed_contracts,
    get_pending_slots,
    get_consume_so_far_per_contract,
)
from pdr_backend.util.timeframestr import Timeframe

# ==========================================================================
# test key/value <-> 725 key/value


@enforce_types
def test_key():
    key = "name"
    key725 = key_to_key725(key)
    assert key725 == Web3.keccak(key.encode("utf-8")).hex()


@enforce_types
def test_value():
    value = "ETH/USDT"
    value725 = value_to_value725(value)
    value_again = value725_to_value(value725)

    assert value == value_again
    assert value == Web3.to_text(hexstr=value725)


@enforce_types
def test_value_None():
    assert value_to_value725(None) is None
    assert value725_to_value(None) is None


# ==========================================================================
# test info <-> info725


@enforce_types
def test_info_to_info725_and_back():
    info = {"pair": "BTC/USDT", "timeframe": "5m", "source": "binance"}
    info725 = [
        {"key": key_to_key725("pair"), "value": value_to_value725("BTC/USDT")},
        {"key": key_to_key725("timeframe"), "value": value_to_value725("5m")},
        {"key": key_to_key725("source"), "value": value_to_value725("binance")},
    ]
    assert info_to_info725(info) == info725
    assert info725_to_info(info725) == info


@enforce_types
def test_info_to_info725_and_back__some_None():
    info = {"pair": "BTC/USDT", "timeframe": "5m", "source": None}
    info725 = [
        {"key": key_to_key725("pair"), "value": value_to_value725("BTC/USDT")},
        {"key": key_to_key725("timeframe"), "value": value_to_value725("5m")},
        {"key": key_to_key725("source"), "value": None},
    ]
    assert info_to_info725(info) == info725
    assert info725_to_info(info725) == info


@enforce_types
def test_info_to_info725__extraval():
    info = {
        "pair": "BTC/USDT",
        "timeframe": "5m",
        "source": "binance",
        "extrakey": "extraval",
    }
    info725 = [
        {"key": key_to_key725("pair"), "value": value_to_value725("BTC/USDT")},
        {"key": key_to_key725("timeframe"), "value": value_to_value725("5m")},
        {"key": key_to_key725("source"), "value": value_to_value725("binance")},
        {"key": key_to_key725("extrakey"), "value": value_to_value725("extraval")},
    ]
    assert info_to_info725(info) == info725


@enforce_types
def test_info_to_info725__missingkey():
    info = {"pair": "BTC/USDT", "timeframe": "5m"}  # no "source"
    info725 = [
        {"key": key_to_key725("pair"), "value": value_to_value725("BTC/USDT")},
        {"key": key_to_key725("timeframe"), "value": value_to_value725("5m")},
        {"key": key_to_key725("source"), "value": None},
    ]
    assert info_to_info725(info) == info725


# ==========================================================================
# test query_subgraph()


@enforce_types
class MockResponse:
    def __init__(self, contract_list: list, status_code: int):
        self.contract_list = contract_list
        self.status_code = status_code
        self.num_queries = 0

    def json(self) -> dict:
        self.num_queries += 1
        if self.num_queries > 1:
            self.contract_list = []
        return {"data": {"predictContracts": self.contract_list}}


@enforce_types
class MockPost:
    def __init__(self, contract_list: list = [], status_code: int = 200):
        self.response = MockResponse(contract_list, status_code)

    def __call__(self, *args, **kwargs):
        return self.response


@enforce_types
def test_query_subgraph_happypath(monkeypatch):
    monkeypatch.setattr(requests, "post", MockPost(status_code=200))
    result = query_subgraph(subgraph_url="foo", query="bar")
    assert result == {"data": {"predictContracts": []}}


@enforce_types
def test_query_subgraph_badpath(monkeypatch):
    monkeypatch.setattr(requests, "post", MockPost(status_code=400))
    with pytest.raises(Exception):
        query_subgraph(subgraph_url="foo", query="bar")


# ==========================================================================
# test query_feed_contracts()


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
    assert isinstance(feed, Feed)

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


# ==========================================================================
# test - pending slots


@enforce_types
def test_get_pending_slots():
    sample_slot_data = [
        {
            "id": "slot1",
            "slot": 1000,
            "trueValues": [],
            "predictContract": {
                "id": "contract1",
                "token": {
                    "id": "token1",
                    "name": "ether",
                    "symbol": "ETH",
                    "nft": {
                        "owner": {"id": "0xowner1"},
                        "nftData": [
                            {
                                "key": key_to_key725("pair"),
                                "value": value_to_value725("ETH/USDT"),
                            },
                            {
                                "key": key_to_key725("timeframe"),
                                "value": value_to_value725("5m"),
                            },
                            {
                                "key": key_to_key725("source"),
                                "value": value_to_value725("binance"),
                            },
                        ],
                    },
                },
                "secondsPerEpoch": 7,
                "secondsPerSubscription": 700,
                "truevalSubmitTimeout": 5,
            },
        }
    ]

    call_count = 0

    def mock_query_subgraph(subgraph_url, query):  # pylint:disable=unused-argument
        nonlocal call_count
        slot_data = sample_slot_data if call_count <= 1 else []
        call_count += 1
        return {"data": {"predictSlots": slot_data}}

    with patch(
        "pdr_backend.subgraph.core_subgraph.query_subgraph", mock_query_subgraph
    ):
        slots = get_pending_slots(
            subgraph_url="foo",
            timestamp=2000,
            owner_addresses=None,
            pair_filter=None,
            timeframe_filter=None,
            source_filter=None,
        )

    assert len(slots) == 2
    slot0 = slots[0]
    assert isinstance(slot0, Slot)
    assert slot0.slot_number == 1000
    assert slot0.feed.name == "ether"


# ==========================================================================
# test - consume so far


@enforce_types
def test_get_consume_so_far_per_contract():
    sample_contract_data = [
        {
            "id": "contract1",
            "token": {
                "id": "token1",
                "name": "ether",
                "symbol": "ETH",
                "orders": [
                    {
                        "createdTimestamp": 1695288424,
                        "consumer": {
                            "id": "0xff8dcdfc0a76e031c72039b7b1cd698f8da81a0a"
                        },
                        "lastPriceValue": "2.4979184013322233",
                    },
                    {
                        "createdTimestamp": 1695288724,
                        "consumer": {
                            "id": "0xff8dcdfc0a76e031c72039b7b1cd698f8da81a0a"
                        },
                        "lastPriceValue": "2.4979184013322233",
                    },
                ],
                "nft": {
                    "owner": {"id": "0xowner1"},
                    "nftData": [
                        {
                            "key": key_to_key725("pair"),
                            "value": value_to_value725("ETH/USDT"),
                        },
                        {
                            "key": key_to_key725("timeframe"),
                            "value": value_to_value725("5m"),
                        },
                        {
                            "key": key_to_key725("source"),
                            "value": value_to_value725("binance"),
                        },
                    ],
                },
            },
            "secondsPerEpoch": 7,
            "secondsPerSubscription": 700,
            "truevalSubmitTimeout": 5,
        }
    ]

    call_count = 0

    def mock_query_subgraph(
        subgraph_url, query, tries, timeout
    ):  # pylint:disable=unused-argument
        nonlocal call_count
        slot_data = sample_contract_data

        if call_count > 0:
            slot_data[0]["token"]["orders"] = []

        call_count += 1
        return {"data": {"predictContracts": slot_data}}

    with patch(
        "pdr_backend.subgraph.core_subgraph.query_subgraph", mock_query_subgraph
    ):
        consumes = get_consume_so_far_per_contract(
            subgraph_url="foo",
            user_address="0xff8dcdfc0a76e031c72039b7b1cd698f8da81a0a",
            since_timestamp=2000,
            contract_addresses=["contract1"],
        )

    assert consumes["contract1"] == approx(6, 0.001)


# ==========================================================================
# test - block number synced


@enforce_types
def test_block_number_is_synced():
    def mock_response(url: str, query: str):  # pylint:disable=unused-argument
        if "number:50" in query:
            return {
                "errors": [
                    {
                        # pylint: disable=line-too-long
                        "message": "Failed to decode `block.number` value: `subgraph QmaGAi4jQw5L8J2xjnofAJb1PX5LLqRvGjsWbVehBELAUx only has data starting at block number 499 and data for block number 500 is therefore not available`"
                    }
                ]
            }

        return {"data": {"predictContracts": [{"id": "sample_id"}]}}

    with patch(
        "pdr_backend.subgraph.core_subgraph.query_subgraph", side_effect=mock_response
    ):
        assert block_number_is_synced("foo", 499) is True
        assert block_number_is_synced("foo", 500) is False
        assert block_number_is_synced("foo", 501) is False
