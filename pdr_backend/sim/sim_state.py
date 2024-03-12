from typing import Dict, List

from enforce_typing import enforce_types

from pdr_backend.util.currency_types import Eth


# pylint: disable=too-many-instance-attributes
@enforce_types
class SimState:
    def __init__(self, init_holdings: Dict[str, Eth]):
        self.holdings: Dict[str, float] = {
            tok: float(amt.amt_eth) for tok, amt in init_holdings.items()
        }
        self.init_loop_attributes()

    def init_loop_attributes(self):
        self.ytrues_test: List[float] = []
        self.probs_up: List[float] = []
        self.pdr_profits_OCEAN: List[float] = []
        self.trader_profits_USD: List[float] = []

    @property
    def ytrues_testhat(self) -> List[bool]:
        return [p > 0.5 for p in self.probs_up]

    @property
    def corrects(self) -> List[bool]:
        return [(p > 0.5) == t
                for p, t in zip(self.probs_up, self.ytrues_test)]

    @property
    def n_correct(self) -> int:
        return sum(self.corrects)

    @property
    def n_trials(self) -> int:
        return len(self.ytrues_test)

    
