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

    def json(self) -> dict:
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
    
    contract1 = {"token": {"nft": {"nftData": info725_list}}}
    contract_list = [contract1]
    monkeypatch.setattr(requests, "post", MockPost(contract_list))
    contracts = get_all_interesting_prediction_contracts(subgraph_url="foo")
    #import pdb; pdb.set_trace()
    #assert contracts == FIXME

