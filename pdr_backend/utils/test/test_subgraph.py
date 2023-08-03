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
        status_code = 200

        @staticmethod
        def json():
            return {"data": {"predictContracts": []}}
        
    subgraph_url = "foo"

    #happy path
    def mock_post(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "post", mock_post)
    contracts = get_all_interesting_prediction_contracts(subgraph_url)
    assert contracts == {}

