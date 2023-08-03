import requests

import pytest

from pdr_backend.utils.subgraph import \
    query_subgraph, get_all_interesting_prediction_contracts

class MockResponse:
    def __init__(self, status_code):
        self.status_code = status_code

    @staticmethod
    def json():
        return {"mock_key": "mock_response"}

def mock_post_happy(*args, **kwargs):
    return MockResponse(status_code=200)

def mock_post_bad(*args, **kwargs):
    return MockResponse(status_code=400)

def test_query_subgraph_happy(monkeypatch):
    monkeypatch.setattr(requests, "post", mock_post_happy)
    result = query_subgraph(subgraph_url="foo", query="bar")
    assert result == {"mock_key": "mock_response"}

def test_query_subgraph_bad(monkeypatch):
    monkeypatch.setattr(requests, "post", mock_post_bad)
    with pytest.raises(Exception):
        query_subgraph(subgraph_url="foo", query="bar")

def test_get_all_interesting_prediction_contracts():
    pass

