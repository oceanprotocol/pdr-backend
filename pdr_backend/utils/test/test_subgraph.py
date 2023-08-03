import requests

from pdr_backend.utils.subgraph import \
    query_subgraph, get_all_interesting_prediction_contracts

def test_subgraph1(monkeypatch):
    class MockResponse:
        @property
        def status_code(self):
            return 200

        @staticmethod
        def json():
            return {"mock_key": "mock_response"}

    def mock_post(*args, **kwargs):
        return MockResponse()

    # apply the monkeypatch for requests.post to mock_post
    monkeypatch.setattr(requests, "post", mock_post)
    
    subgraph_url = "foo"
    query = "bar"
    result = query_subgraph(subgraph_url, query)

    assert result == {"mock_key": "mock_response"}

def test_get_all_interesting_prediction_contracts():
    pass

