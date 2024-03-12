from typing import Dict, List

from enforce_typing import enforce_types

from pdr_backend.util.currency_types import Eth


@enforce_types
class ClassifierMetrics:
    def __init__(self):
        # 'i' is iteration number i
        self.acc_ests: List[float] = []  # [i] : %-correct
        self.acc_ls: List[float] = []  # [i] : %-correct-lower
        self.acc_us: List[float] = []  # [i] : %-correct-upper

        self.f1s: List[float] = []  # [i] : f1-score
        self.precisions: List[float] = []  # [i] : precision
        self.recalls: List[float] = []  # [i] : recall

    def update(self, acc_est, acc_l, acc_u, f1, precision, recall):
        self.acc_ests.append(acc_est)
        self.acc_ls.append(acc_l)
        self.acc_us.append(acc_u)

        self.f1s.append(f1)
        self.precisions.append(precision)
        self.recalls.append(recall)


# pylint: disable=too-many-instance-attributes
@enforce_types
class SimState:
    def __init__(self, init_holdings: Dict[str, Eth]):
        self.holdings: Dict[str, float] = {
            tok: float(amt.amt_eth) for tok, amt in init_holdings.items()
        }
        self.init_loop_attributes()

    def init_loop_attributes(self):
        # 'i' is iteration number i

        # base data
        self.ytrues: List[bool] = []  # [i] : was-truly-up
        self.probs_up: List[float] = []  # [i] : predicted-prob-up

        # classifier metrics
        self.clm = ClassifierMetrics()

        # profits
        self.pdr_profits_OCEAN: List[float] = []  # [i] : predictoor-profit
        self.trader_profits_USD: List[float] = []  # [i] : trader-profit

    @property
    def ytrues_hat(self) -> List[bool]:
        return [p > 0.5 for p in self.probs_up]

    @property
    def n_correct(self) -> int:
        return sum((p > 0.5) == t for p, t in zip(self.probs_up, self.ytrues))
