from typing import Dict
from unittest.mock import patch

from enforce_typing import enforce_types

from pdr_backend.subgraph.subgraph_payout import (
    Payout,
    get_payout_query,
    fetch_payouts,
)
from pdr_backend.util.time_types import UnixTimeSeconds

# pylint: disable=line-too-long
MOCK_PAYOUT_QUERY_RESPONSE = {
    "data": {
        "predictPayouts": [
            {
                "id": "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1696880700-0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
                "timestamp": 1698527000,
                "payout": "0",
                "predictedValue": True,
                "prediction": {
                    "stake": "1.2",
                    "user": {"id": "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd"},
                    "slot": {
                        "id": "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1696880700",
                        "predictContract": {
                            "id": "0x18f54cc21b7a2fdd011bea06bba7801b280e3151",
                            "token": {"name": "ADA/USDT"},
                        },
                        "revenue": "0.919372744934776618",
                        "roundSumStakesUp": "7.635901006590730052",
                        "roundSumStakes": "17.728238320965607921",
                    },
                },
            }
        ]
    }
}

MOCK_PAYOUT_QUERY_SECOND_RESPONSE: Dict[str, dict] = {"data": {"predictPayouts": []}}


def test_get_payout_query():
    payout_query = get_payout_query(
        ["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"],
        UnixTimeSeconds(1622547000),
        UnixTimeSeconds(1622548800),
        1,
        1,
    )

    assert "1622547000" in payout_query
    assert "1622548800" in payout_query
    assert "0x18f54cc21b7a2fdd011bea06bba7801b280e3151" in payout_query


@enforce_types
@patch("pdr_backend.subgraph.subgraph_payout.query_subgraph")
def test_fetch_payouts(mock_query_subgraph):
    mock_query_subgraph.side_effect = [
        MOCK_PAYOUT_QUERY_RESPONSE,
        MOCK_PAYOUT_QUERY_SECOND_RESPONSE,
    ]

    payouts = fetch_payouts(
        addresses=["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"],
        start_ts=UnixTimeSeconds(1622547000),
        end_ts=UnixTimeSeconds(1622548800),
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
    assert payouts[0].predictedValue is True
    assert payouts[0].user == "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd"
    assert payouts[0].stake == float(1.2)
    assert mock_query_subgraph.call_count == 1
