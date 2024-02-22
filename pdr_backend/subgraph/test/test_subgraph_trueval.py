from unittest.mock import patch

from enforce_typing import enforce_types

from pdr_backend.subgraph.subgraph_trueval import (
    Trueval,
    get_truevals_query,
    fetch_truevals,
)

# pylint: disable=line-too-long
MOCK_TRUEVAL_QUERY_RESPONSE = {
    "data": {
        "predictTrueVals": [
            {
                "id": "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1698527100",
                "timestamp": 1698527000,
                "trueValue": True,
                "slot": {
                    "slot": 1698527100,
                    "predictContract": {
                        "token": {"name": "ADA/USDT"},
                    },
                },
            }
        ]
    }
}


def test_get_trueval_query():
    trueval_query = get_truevals_query(
        ["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"], 1622547000, 1622548800, 1000, 0
    )

    assert "1622547000" in trueval_query
    assert "1622548800" in trueval_query
    assert "0x18f54cc21b7a2fdd011bea06bba7801b280e3151" in trueval_query


@enforce_types
@patch("pdr_backend.subgraph.subgraph_trueval.query_subgraph")
def test_fetch_filtered_truevals(mock_query_subgraph):
    mock_query_subgraph.return_value = MOCK_TRUEVAL_QUERY_RESPONSE

    truevals = fetch_truevals(
        start_ts=1698526000,
        end_ts=1698528000,
        first=1000,
        skip=0,
        addresses=["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"],
        network="mainnet",
    )
    print(truevals)
    assert len(truevals) == 1
    assert isinstance(truevals[0], Trueval)
    assert truevals[0].ID == "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1698527100"
    assert truevals[0].token == "ADA/USDT"
    assert truevals[0].timestamp == 1698527000
    assert truevals[0].slot == 1698527100
    assert truevals[0].truevalue is True
    assert mock_query_subgraph.call_count == 1
