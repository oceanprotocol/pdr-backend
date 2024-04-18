from typing import Dict, List, Tuple

from enforce_typing import enforce_types

from pdr_backend.subgraph.subgraph_feed import SubgraphFeed
from pdr_backend.util.currency_types import Eth
from pdr_backend.util.time_types import UnixTimeS


@enforce_types
class StakeTup(Tuple[SubgraphFeed, Eth, Eth]):
    """(feed, stake_up, stake_down)"""


@enforce_types
class StakeTups(List[StakeTup]):
    pass


class StakesPerSlot:
    def __init__(self):
        self.target_slots: Dict[UnixTimeS, StakeTups] = {}

    @property
    def slots(self) -> List[UnixTimeS]:
        """@return -- list of timeslots handled so far"""
        return list(self.target_slots.keys())

    @enforce_types
    def add_stake_at_slot(
        self,
        timeslot: UnixTimeS,
        stake_tup: StakeTup,
    ):
        if timeslot not in self.target_slots:
            self.target_slots[timeslot] = StakeTups([])
        self.target_slots[timeslot].append(stake_tup)

    @enforce_types
    def get_stakes_at_slot(self, timeslot: UnixTimeS) -> StakeTups:
        """@return -- predictions at the specified timeslot"""
        tups = self.target_slots.get(timeslot, StakeTups([]))
        return tups

    @enforce_types
    def get_stake_lists(
        self, timeslot: UnixTimeS
    ) -> Tuple[List[Eth], List[Eth], List[str]]:
        stakes_up: List[Eth] = []
        stakes_down: List[Eth] = []
        feed_addrs: List[str] = []

        for feed, stake_up, stake_down in self.get_stakes_at_slot(timeslot):
            stakes_up.append(stake_up)
            stakes_down.append(stake_down)
            feed_addrs.append(feed.address)

        return stakes_up, stakes_down, feed_addrs
