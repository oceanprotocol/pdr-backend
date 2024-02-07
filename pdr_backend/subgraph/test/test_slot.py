from enforce_typing import enforce_types

from pdr_backend.subgraph.slot import Slot, mock_slots


@enforce_types
def test_slots():
    slots = mock_slots()
    
    assert len(slots) == 6
    assert isinstance(slots[0], Slot)
    assert isinstance(slots[1], Slot)
    assert slots[0].ID == "0x8165caab33131a4ddbf7dc79f0a8a4920b0b2553-1696838400"
    assert slots[1].ID == "0x8165caab33131a4ddbf7dc79f0a8a4920b0b2553-1696838100"
