from typing import List, Optional, Union

from enforce_typing import enforce_types


# pylint: disable=too-many-instance-attributes
@enforce_types
class SimState:
    def __init__(self):
        self.init_loop_attributes()
        self.iter_number = 0

    def init_loop_attributes(self):
        # 'i' is iteration number i

        # base data
        self.probs_up: List[float] = []  # [i] : predicted-prob-up

        # profits
        self.profits: List[float] = []  # [i] : trader_profit
