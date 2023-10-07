from unittest.mock import patch

from enforce_typing import enforce_types
import pytest
import requests
from web3 import Web3
from pytest import approx

from pdr_backend.models.slot import Slot
from pdr_backend.util.subgraph import (
    block_number_is_synced,
    key_to_725,
    value_to_725,
    value_from_725,
    info_from_725,
    query_subgraph,
    query_feed_contracts,
    get_pending_slots,
    get_consume_so_far_per_contract,
)


@enforce_types
def test_key():
    key = "name"
    key725 = key_to_725(key)
    assert key725 == Web3.keccak(key.encode("utf-8")).hex()


@enforce_types
def test_value():
    value = "ETH/USDT"
    value725 = value_to_725(value)
    value_again = value_from_725(value725)

    assert value == value_again
    assert value == Web3.to_text(hexstr=value725)


@enforce_types
def test_info_from_725():
    info725_list = [
        {"key": key_to_725("pair"), "value": value_to_725("ETH/USDT")},
        {"key": key_to_725("timeframe"), "value": value_to_725("5m")},
    ]
    info_dict = info_from_725(info725_list)
    assert info_dict == {
        "pair": "ETH/USDT",
        "timeframe": "5m",
        "base": None,
        "quote": None,
        "source": None,
    }


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


@enforce_types
def test_get_contracts_emptychain(monkeypatch):
    contract_list = []
    monkeypatch.setattr(requests, "post", MockPost(contract_list))
    contracts = query_feed_contracts(subgraph_url="foo")
    assert contracts == {}


@enforce_types
def test_query_feed_contracts_fullchain(monkeypatch):
    # This test is a simple-as-possible happy path. Start here.
    # Then follow up with test_filter() below, which is complex but thorough
    info725_list = [
        {"key": key_to_725("pair"), "value": value_to_725("ETH/USDT")},
        {"key": key_to_725("timeframe"), "value": value_to_725("5m")},
    ]

    contract1 = {
        "id": "contract1",
        "token": {
            "id": "token1",
            "name": "ether",
            "symbol": "ETH",
            "nft": {
                "owner": {
                    "id": "0xowner",
                },
                "nftData": info725_list,
            },
        },
        "secondsPerEpoch": 7,
        "secondsPerSubscription": 700,
        "truevalSubmitTimeout": 5,
    }
    contract_list = [contract1]
    monkeypatch.setattr(requests, "post", MockPost(contract_list))
    feed_dicts = query_feed_contracts(subgraph_url="foo")
    assert list(feed_dicts.keys()) == ["contract1"]
    feed_dict = feed_dicts["contract1"]
    assert feed_dict == {
        "name": "ether",
        "address": "contract1",
        "symbol": "ETH",
        "seconds_per_epoch": 7,
        "seconds_per_subscription": 700,
        "trueval_submit_timeout": 5,
        "owner": "0xowner",
        "last_submited_epoch": 0,
        "pair": "ETH/USDT",
        "base": None,
        "quote": None,
        "source": None,
        "timeframe": "5m",
    }


@enforce_types
@pytest.mark.parametrize(
    "expect_result, pairs, timeframes, sources, owners",
    [
        (True, None, None, None, None),
        (True, "ETH/USDT", "5m", "binance", "0xowner1"),
        (True, "ETH/USDT,BTC/USDT", "5m,15m", "binance,kraken", "0xowner1,o2"),
        (True, "ETH/USDT", None, None, None),
        (False, "BTC/USDT", None, None, None),
        (True, "ETH/USDT,BTC/USDT", None, None, None),
        (True, None, "5m", None, None),
        (False, None, "15m", None, None),
        (True, None, "5m,15m", None, None),
        (True, None, None, "binance", None),
        (False, None, None, "kraken", None),
        (True, None, None, "binance,kraken", None),
        (True, None, None, None, "0xowner1"),
        (False, None, None, None, "owner2"),
        (True, None, None, None, "0xowner1,owner2"),
        (True, None, None, None, ""),
        (True, "", "", "", ""),
        (True, None, None, "", "0xowner1,owner2"),
    ],
)
def test_filter(monkeypatch, expect_result, pairs, timeframes, sources, owners):
    info725_list = [
        {"key": key_to_725("pair"), "value": value_to_725("ETH/USDT")},
        {"key": key_to_725("timeframe"), "value": value_to_725("5m")},
        {"key": key_to_725("source"), "value": value_to_725("binance")},
        {"key": key_to_725("base"), "value": value_to_725("USDT")},
        {"key": key_to_725("quote"), "value": value_to_725("1400.1")},
        {"key": key_to_725("extra1"), "value": value_to_725("extra1_value")},
        {"key": key_to_725("extra2"), "value": value_to_725("extra2_value")},
    ]

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
                "nftData": info725_list,
            },
        },
        "secondsPerEpoch": 7,
        "secondsPerSubscription": 700,
        "truevalSubmitTimeout": 5,
    }

    contract_list = [contract1]

    monkeypatch.setattr(requests, "post", MockPost(contract_list))
    feed_dicts = query_feed_contracts("foo", pairs, timeframes, sources, owners)

    assert bool(feed_dicts) == bool(expect_result)


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
                                "key": key_to_725("pair"),
                                "value": value_to_725("ETH/USDT"),
                            },
                            {
                                "key": key_to_725("timeframe"),
                                "value": value_to_725("5m"),
                            },
                            {
                                "key": key_to_725("source"),
                                "value": value_to_725("binance"),
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

    with patch("pdr_backend.util.subgraph.query_subgraph", mock_query_subgraph):
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
                            "key": key_to_725("pair"),
                            "value": value_to_725("ETH/USDT"),
                        },
                        {
                            "key": key_to_725("timeframe"),
                            "value": value_to_725("5m"),
                        },
                        {
                            "key": key_to_725("source"),
                            "value": value_to_725("binance"),
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

    def mock_query_subgraph(subgraph_url, query):  # pylint:disable=unused-argument
        nonlocal call_count
        slot_data = sample_contract_data

        if call_count > 0:
            slot_data[0]["token"]["orders"] = []

        call_count += 1
        return {"data": {"predictContracts": slot_data}}

    with patch("pdr_backend.util.subgraph.query_subgraph", mock_query_subgraph):
        consumes = get_consume_so_far_per_contract(
            subgraph_url="foo",
            user_address="0xff8dcdfc0a76e031c72039b7b1cd698f8da81a0a",
            since_timestamp=2000,
            contract_addresses=["contract1"],
        )

    assert consumes["contract1"] == approx(6, 0.001)


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

    with patch("pdr_backend.util.subgraph.query_subgraph", side_effect=mock_response):
        assert block_number_is_synced("foo", 499) is True
        assert block_number_is_synced("foo", 500) is False
        assert block_number_is_synced("foo", 501) is False
