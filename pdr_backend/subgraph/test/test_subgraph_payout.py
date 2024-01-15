from unittest.mock import patch

from enforce_typing import enforce_types

from pdr_backend.subgraph.subgraph_payout import (
    Payout,
    get_payout_query,
    fetch_payouts,
)

# pylint: disable=line-too-long
MOCK_PAYOUT_QUERY_RESPONSE = {
    "data": {
        "predictPayouts": [
            {
                "id": "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1696880700-0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
                "timestamp": 1698527000,
                "payout": "0",
                "prediction": {
                    "user": {"id": "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd"},
                    "slot": {
                        "id": "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1696880700",
                        "predictContract": {
                            "id": "0x18f54cc21b7a2fdd011bea06bba7801b280e3151",
                            "token": {"name": "ADA/USDT"},
                        },
                    },
                },
            }
        ]
    }
}


def test_get_payout_query():
    payout_query = get_payout_query(
        ["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"], 1622547000, 1622548800, 1, 1
    )

    assert "1622547000" in payout_query
    assert "1622548800" in payout_query
    assert "0x18f54cc21b7a2fdd011bea06bba7801b280e3151" in payout_query


@enforce_types
@patch("pdr_backend.subgraph.subgraph_payout.query_subgraph")
def test_fetch_payouts(mock_query_subgraph):
    mock_query_subgraph.return_value = MOCK_PAYOUT_QUERY_RESPONSE

    payouts = fetch_payouts(
        addresses=["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"],
        start_ts=1622547000,
        end_ts=1622548800,
        skip=1,
        network="mainnet",
    )
    assert len(payouts) == 1
    assert isinstance(payouts[0], Payout)
    assert (
        payouts[0].ID
        == "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1696880700-0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd"
    )
    assert payouts[0].token == "ADA/USDT"
    assert payouts[0].timestamp == 1698527000
    assert payouts[0].slot == 1696880700
    assert payouts[0].payout == float(0)
    assert mock_query_subgraph.call_count == 1
