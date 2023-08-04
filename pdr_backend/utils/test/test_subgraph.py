import requests

from enforce_typing import enforce_types
import pytest
from web3 import Web3

from pdr_backend.utils.subgraph import (
    key_to_725, value_to_725, value_from_725, info_from_725,
    query_subgraph, get_all_interesting_prediction_contracts,
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
        {"key":key_to_725("pair"), "value":value_to_725("ETH/USDT")},
        {"key":key_to_725("timeframe"), "value":value_to_725("5m")},
        ]
    info_dict = info_from_725(info725_list)
    assert info_dict == {
        "pair": "ETH/USDT", 
        "timeframe": "5m",
        }

    
@enforce_types
class MockResponse:
    def __init__(self, contract_list:list, status_code:int):
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
    def __init__(self, contract_list: list = [], status_code:int = 200):
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
def test_get_all_interesting_prediction_contracts_emptychain(monkeypatch):
    contract_list = []
    monkeypatch.setattr(requests, "post", MockPost(contract_list))
    contracts = get_all_interesting_prediction_contracts(subgraph_url="foo")
    assert contracts == {}


@enforce_types
def test_get_all_interesting_prediction_contracts_fullchain(monkeypatch):
    info725_list = [
        {"key":key_to_725("pair"), "value":value_to_725("ETH/USDT")},
        {"key":key_to_725("timeframe"), "value":value_to_725("5m")},
        ]
    
    contract1 = {
        "id" : "contract1",
        "token": {
            "id": "token1",
            "name": "ether",
            "symbol": "ETH",
            "nft": {
                "owner": {
                    "id": "owner1",
                },
                "nftData": info725_list,
            },
        },
        "blocksPerEpoch": 7,
        "blocksPerSubscription": 700,
        "truevalSubmitTimeoutBlock": 5,
    }
    contract_list = [contract1]
    monkeypatch.setattr(requests, "post", MockPost(contract_list))
    contracts = get_all_interesting_prediction_contracts(subgraph_url="foo")
    assert contracts == {
        "contract1": {
            "name": "ether",
            "address": "contract1",
            "symbol": "ETH",
            "blocks_per_epoch": 7,
            "blocks_per_subscription": 700,
            "last_submited_epoch": 0,
            "pair": "ETH/USDT",
            "base": None,
            "quote": None,
            "source": None,
            "timeframe": "5m"
        }
    }


@enforce_types
def test_filter(monkeypatch):
    N, T, F = None, True, False
    for (expect_result, tup) in [
            (T, (N, N, N, N)),
            (T, ("ETH/USDT", "5m", "binance", "owner1")),
            (T, ("ETH/USDT,BTC/USDT", "5m,15m", "binance,kraken", "owner1,o2")),
            
            (T, ("ETH/USDT", N, N, N)),
            (F, ("BTC/USDT", N, N, N)),
            (T, ("ETH/USDT,BTC/USDT", N, N, N)),
            
            (T, (N, "5m", N, N)),
            (F, (N, "15m", N, N)),
            (T, (N, "5m,15m", N, N)),
            
            (T, (N, N, "binance", N)),
            (F, (N, N, "kraken", N)),
            (T, (N, N, "binance,kraken", N)),
            
            (T, (N, N, N, "owner1")),
            (F, (N, N, N, "owner2")),
            (T, (N, N, N, "owner1,owner2")),
    ]:
        _test_filter(monkeypatch, expect_result, tup)

@enforce_types
def _test_filter(monkeypatch, expect_result:bool, tup:tuple):
    pairs, timeframes, sources, owners = tup
    info725_list = [
        {"key":key_to_725("pair"), "value":value_to_725("ETH/USDT")},
        {"key":key_to_725("timeframe"), "value":value_to_725("5m")},
        {"key":key_to_725("source"), "value":value_to_725("binance")},
        
        {"key":key_to_725("base"), "value":value_to_725("USDT")},
        {"key":key_to_725("quote"), "value":value_to_725("1400.1")},
        
        {"key":key_to_725("extra1"), "value":value_to_725("extra1_value")},
        {"key":key_to_725("extra2"), "value":value_to_725("extra2_value")},
        ]
    
    contract1 = {
        "id" : "contract1",
        "token": {
            "id": "token1",
            "name": "ether",
            "symbol": "ETH",
            "nft": {
                "owner": {
                    "id": "owner1",
                },
                "nftData": info725_list,
            },
        },
        "blocksPerEpoch": 7,
        "blocksPerSubscription": 700,
        "truevalSubmitTimeoutBlock": 5,
    }
    
    contract_list = [contract1]
    
    monkeypatch.setattr(requests, "post", MockPost(contract_list))
    contracts = get_all_interesting_prediction_contracts(
        "foo", pairs, timeframes, sources, owners)
    
    assert bool(contracts) == bool(expect_result)
    

