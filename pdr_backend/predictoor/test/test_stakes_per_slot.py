from typing import Dict, List, Tuple
from unittest.mock import Mock

from enforce_typing import enforce_types

from pdr_backend.predictoor.stakes_per_slot import (
    StakeTup,
    StakeTups,
    StakesPerSlot,
)
from pdr_backend.subgraph.subgraph_feed import SubgraphFeed
from pdr_backend.util.currency_types import Eth
from pdr_backend.util.time_types import UnixTimeS

FEED0 = Mock(spec=SubgraphFeed)
FEED1 = Mock(spec=SubgraphFeed)
FEED0.address = "0xFeed0"
FEED1.address = "0xFeed1"

STAKE_UP0, STAKE_DOWN0 = Eth(10.0), Eth(20.0)
STAKE_UP1, STAKE_DOWN1 = Eth(11.0), Eth(21.0)
STAKE_UP2, STAKE_DOWN2 = Eth(12.0), Eth(22.0)
STAKE_UP3, STAKE_DOWN3 = Eth(13.0), Eth(23.0)

TUP0 = StakeTup((FEED0, STAKE_UP0, STAKE_DOWN0))
TUP1 = StakeTup((FEED0, STAKE_UP1, STAKE_DOWN1))
TUP2 = StakeTup((FEED1, STAKE_UP2, STAKE_DOWN2))
TUP3 = StakeTup((FEED1, STAKE_UP3, STAKE_DOWN3))

TIMESLOT0 = UnixTimeS(1000)
TIMESLOT1 = UnixTimeS(2000)


@enforce_types
def test_StakeTup():
    assert TUP0[0] == FEED0
    assert TUP0[1] == STAKE_UP0
    assert TUP0[2] == STAKE_DOWN0


@enforce_types
def test_StakeTups():
    tups = StakeTups([TUP0, TUP1])
    assert tups[0] == TUP0
    assert tups[1] == TUP1


@enforce_types
def test_StakesPerSlot():
    # empty to start
    stakes = StakesPerSlot()
    assert stakes.target_slots == {}
    assert stakes.slots == []
    assert stakes.get_stakes_at_slot(TIMESLOT0) == []
    assert stakes.get_stakes_at_slot(TIMESLOT1) == []

    # add at one timeslot
    stakes.add_stake_at_slot(TIMESLOT0, TUP0)
    stakes.add_stake_at_slot(TIMESLOT0, TUP1)
    assert stakes.slots == [TIMESLOT0]
    assert stakes.get_stakes_at_slot(TIMESLOT0) == [TUP0, TUP1]
    assert stakes.get_stakes_at_slot(TIMESLOT1) == []

    # add at another timeslot
    stakes.add_stake_at_slot(TIMESLOT1, TUP2)
    stakes.add_stake_at_slot(TIMESLOT1, TUP3)
    assert stakes.slots == [TIMESLOT0, TIMESLOT1]
    assert stakes.get_stakes_at_slot(TIMESLOT0) == [TUP0, TUP1]
    assert stakes.get_stakes_at_slot(TIMESLOT1) == [TUP2, TUP3]

    # test get_stake_lists
    (stakes_up, stakes_down, feed_addrs) = stakes.get_stake_lists(TIMESLOT0)
    assert stakes_up == [STAKE_UP0, STAKE_UP1]
    assert stakes_down == [STAKE_DOWN0, STAKE_DOWN1]
    assert feed_addrs == ["0xFeed0", "0xFeed0"]

    (stakes_up, stakes_down, feed_addrs) = stakes.get_stake_lists(TIMESLOT1)
    assert stakes_up == [STAKE_UP2, STAKE_UP3]
    assert stakes_down == [STAKE_DOWN2, STAKE_DOWN3]
    assert feed_addrs == ["0xFeed1", "0xFeed1"]
