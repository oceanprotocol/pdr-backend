from pdr_backend.models.slot import Slot
from pdr_backend.models.feed import SubgraphFeed


def test_slot_initialization():
    feed = SubgraphFeed(
        "Contract Name",
        "0x12345",
        "test",
        60,
        15,
        "0xowner",
        "BTC/ETH",
        "1h",
        "binance",
    )

    slot_number = 5
    slot = Slot(slot_number, feed)

    assert slot.slot_number == slot_number
    assert slot.feed == feed
    assert isinstance(slot.feed, SubgraphFeed)
