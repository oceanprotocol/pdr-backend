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
        self.accs_train: List[float] = []
        self.ybools_test: List[float] = []
        self.ybools_testhat: List[float] = []
        self.probs_up: List[float] = []
        self.corrects: List[bool] = []
        self.trader_profits_USD: List[float] = []
        self.pdr_profits_OCEAN: List[float] = []
