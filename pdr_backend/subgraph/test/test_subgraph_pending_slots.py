from unittest.mock import patch

from enforce_typing import enforce_types

from pdr_backend.contract.slot import Slot
from pdr_backend.subgraph.info725 import key_to_key725, value_to_value725
from pdr_backend.subgraph.subgraph_pending_slots import get_pending_slots

SAMPLE_SLOT_DATA = [
    {
        "id": "slot1",
        "slot": 1000,
        "trueValues": [],
        "predictContract": {
            "id": "contract1",
            "token": {
                "id": "token1",
                "name": "ether",
                "symbol": "ETH",
                "nft": {
                    "owner": {"id": "0xowner1"},
                    "nftData": [
                        {
                            "key": key_to_key725("pair"),
                            "value": value_to_value725("ETH/USDT"),
                        },
                        {
                            "key": key_to_key725("timeframe"),
                            "value": value_to_value725("5m"),
                        },
                        {
                            "key": key_to_key725("source"),
                            "value": value_to_value725("binance"),
                        },
                    ],
                },
            },
            "secondsPerEpoch": 7,
            "secondsPerSubscription": 700,
            "truevalSubmitTimeout": 5,
        },
    }
]


@enforce_types
def test_get_pending_slots():
    call_count = 0

    def mock_query_subgraph(subgraph_url, query):  # pylint:disable=unused-argument
        nonlocal call_count
        slot_data = SAMPLE_SLOT_DATA if call_count <= 1 else []
        call_count += 1
        return {"data": {"predictSlots": slot_data}}

    PATH = "pdr_backend.subgraph.subgraph_pending_slots"
    with patch(f"{PATH}.query_subgraph", mock_query_subgraph):
        slots = get_pending_slots(
            subgraph_url="foo",
            timestamp=2000,
            owner_addresses=None,
            pair_filter=None,
            timeframe_filter=None,
            source_filter=None,
        )

    assert len(slots) == 2
    slot0 = slots[0]
    assert isinstance(slot0, Slot)
    assert slot0.slot_number == 1000
    assert slot0.feed.name == "ether"
