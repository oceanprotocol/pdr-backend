from unittest.mock import patch

from enforce_typing import enforce_types

from pdr_backend.subgraph.subgraph_pending_payouts import query_pending_payouts

SAMPLE_PENDING_DATA = [
    {
        "id": "slot1",
        "timestamp": 1000,
        "slot": {
            "id": "slot1",
            "slot": 2000,
            "predictContract": {
                "id": "contract1",
            },
        },
    }
]


@enforce_types
def test_query_pending_payouts():
    call_count = 0

    def mock_query_subgraph(subgraph_url, query):  # pylint:disable=unused-argument
        nonlocal call_count
        pending_payout_data = SAMPLE_PENDING_DATA if call_count < 1 else []
        call_count += 1
        return {"data": {"predictPredictions": pending_payout_data}}

    PATH = "pdr_backend.subgraph.subgraph_pending_payouts"
    with patch(f"{PATH}.query_subgraph", mock_query_subgraph):
        pending_payouts = query_pending_payouts(
            subgraph_url="foo",
            addr="0x123",
        )

    assert pending_payouts == {"contract1": [2000]}


@enforce_types
def test_query_pending_payouts_edge_cases(capfd):
    def mock_query_subgraph(subgraph_url, query):
        return {"data": {}}

    PATH = "pdr_backend.subgraph.subgraph_pending_payouts"
    with patch(f"{PATH}.query_subgraph", mock_query_subgraph):
        query_pending_payouts(
            subgraph_url="foo",
            addr="0x123",
        )

    def mock_query_subgraph_2(subgraph_url, query):
        return {"data": {"predictPredictions": []}}

    with patch(f"{PATH}.query_subgraph", mock_query_subgraph_2):
        query_pending_payouts(
            subgraph_url="foo",
            addr="0x123",
        )
