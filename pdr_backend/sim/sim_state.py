from typing import Dict, List, Optional, Union

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

    @staticmethod
    def recent_metrics_names() -> List[str]:
        return ["profit"]

    def recent_metrics(
        self, extras: Optional[List[str]] = None
    ) -> List[Union[int, float]]:
        """Return most recent aimodel metrics + profit metrics"""
        rm = {
            "profit": self.profits[-1],
        }
        if extras and "prob_up" in extras:
            rm["prob_up"] = self.probs_up[-1]

        return rm
