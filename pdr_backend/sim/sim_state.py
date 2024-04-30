from typing import Dict, List, Union

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

        self.losses: List[float] = []  # [i] : log-loss

    def update(self, acc_est, acc_l, acc_u, f1, precision, recall, loss):
        self.acc_ests.append(acc_est)
        self.acc_ls.append(acc_l)
        self.acc_us.append(acc_u)

        self.f1s.append(f1)
        self.precisions.append(precision)
        self.recalls.append(recall)

        self.losses.append(loss)

    @staticmethod
    def recent_metrics_names() -> List[str]:
        return ["acc_est", "acc_l", "acc_u", "f1", "precision", "recall", "loss"]

    def recent_metrics(self) -> List[Union[int, float]]:
        """Return most recent classifier metrics"""
        assert self.acc_ests, "must have >0 entries to call this"
        return [
            self.acc_ests[-1],
            self.acc_ls[-1],
            self.acc_us[-1],
            self.f1s[-1],
            self.precisions[-1],
            self.recalls[-1],
            self.losses[-1],
        ]


# pylint: disable=too-many-instance-attributes
@enforce_types
class SimState:
    def __init__(self, init_holdings: Dict[str, Eth]):
        self.holdings: Dict[str, float] = {
            tok: float(amt.amt_eth) for tok, amt in init_holdings.items()
        }
        self.init_loop_attributes()
        self.iter_number = 0

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

    @staticmethod
    def recent_metrics_names() -> List[str]:
        """Names of most recent metrics. Use eg for csv header."""
        return ClassifierMetrics.recent_metrics_names() + [
            "pdr_profit_OCEAN",
            "trader_profit_USD",
        ]

    def recent_metrics(self) -> List[Union[int, float]]:
        """Return most recent classifier metrics + profit metrics"""
        return self.clm.recent_metrics() + [
            self.pdr_profits_OCEAN[-1],
            self.trader_profits_USD[-1],
        ]

    @property
    def ytrues_hat(self) -> List[bool]:
        return [p > 0.5 for p in self.probs_up]

    @property
    def n_correct(self) -> int:
        return sum((p > 0.5) == t for p, t in zip(self.probs_up, self.ytrues))
