import requests

import pytest

from pdr_backend.utils.subgraph import \
    query_subgraph, get_all_interesting_prediction_contracts

def test_query_subgraph(monkeypatch):
    class MockResponse:
        def __init__(self, status_code):
            self.status_code = status_code

        @staticmethod
        def json():
            return {"mock_key": "mock_response"}
        
    subgraph_url, query = "foo", "bar"

    #happy path
    def mock_post_happy(*args, **kwargs):
        return MockResponse(status_code=200)

    monkeypatch.setattr(requests, "post", mock_post_happy)
    result = query_subgraph(subgraph_url, query)
    assert result == {"mock_key": "mock_response"}

    #bad path
    def mock_post_bad(*args, **kwargs):
        return MockResponse(status_code=400)

    monkeypatch.setattr(requests, "post", mock_post_bad)
    with pytest.raises(Exception):
        query_subgraph(subgraph_url, query)

def test_get_all_interesting_prediction_contracts(monkeypatch):    
    class MockResponse:
        def __init__(self, contracts: list = [], status_code:int = 200):
            self.contracts = contracts
            self.status_code = status_code

        @staticmethod
        def json():
            return {"data": {"predictContracts": contracts}}
        
    subgraph_url = "foo"

    #happy path
    class MockPost:
        def __init__(self, contracts):
            self.response = MockResponse(contracts)
        def __call__(self, *args, **kwargs):
            return self.response

    monkeypatch.setattr(requests, "post", MockPost([]))
    contracts = get_all_interesting_prediction_contracts(subgraph_url)
    assert contracts == {}

