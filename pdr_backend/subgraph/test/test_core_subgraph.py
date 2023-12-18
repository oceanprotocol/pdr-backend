from enforce_typing import enforce_types
import pytest
import requests

from pdr_backend.subgraph.core_subgraph import query_subgraph
from pdr_backend.subgraph.test.resources import MockPost


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
