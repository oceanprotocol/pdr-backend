from typing import Dict, List, Optional, Union

from enforce_typing import enforce_types


@enforce_types
class AimodelMetrics:
    # pylint: disable=too-many-instance-attributes

    def __init__(self):
        # 'i' is iteration number i
        self.acc_ests: List[float] = []  # [i] : %-correct
        self.acc_ls: List[float] = []  # [i] : %-correct-lower
        self.acc_us: List[float] = []  # [i] : %-correct-upper

        self.f1s: List[float] = []  # [i] : f1-score
        self.precisions: List[float] = []  # [i] : precision
        self.recalls: List[float] = []  # [i] : recall

        self.losses: List[float] = []  # [i] : log-loss

        self.yerrs: List[float] = []  # [i] : regressor pred'n errs, w/ sign

    def update(self, acc_est, acc_l, acc_u, f1, precision, recall, loss, yerr):
        self.acc_ests.append(acc_est)
        self.acc_ls.append(acc_l)
        self.acc_us.append(acc_u)

        self.f1s.append(f1)
        self.precisions.append(precision)
        self.recalls.append(recall)

        self.losses.append(loss)

        self.yerrs.append(yerr)

    @staticmethod
    def recent_metrics_names() -> List[str]:
        return [
            "acc_est",
            "acc_l",
            "acc_u",
            "f1",
            "precision",
            "recall",
            "loss",
            "yerr",
        ]

    def recent_metrics(self) -> Dict[str, Union[int, float, None]]:
        """Return most recent aimodel metrics"""
        if not self.acc_ests:
            return {key: None for key in AimodelMetrics.recent_metrics_names()}

        return {
            "acc_est": self.acc_ests[-1],
            "acc_l": self.acc_ls[-1],
            "acc_u": self.acc_us[-1],
            "f1": self.f1s[-1],
            "precision": self.precisions[-1],
            "recall": self.recalls[-1],
            "loss": self.losses[-1],
            "yerr": self.yerrs[-1],
        }


# pylint: disable=too-many-instance-attributes
@enforce_types
class SimState:
    def __init__(self):
        self.init_loop_attributes()
        self.iter_number = 0

    def init_loop_attributes(self):
        # 'i' is iteration number i

        # base data for UP classifier
        self.ytrues_UP: List[bool] = []  # [i] : true value
        self.ytrues_hat_UP: List[bool] = []  # [i] : model pred. value
        self.probs_up_UP: List[float] = []  # [i] : model's pred. probability 

        # base data for DOWN classifier
        self.ytrues_DOWN: List[bool] = []  # [i] : true value
        self.ytrues_hat_DOWN: List[bool] = []  # [i] : model pred. value
        self.probs_up_DOWN: List[float] = []  # [i] : model's pred. probability

        # aimodel metrics
        self.aim = AimodelMetrics()

        # profits
        self.pdr_profits_OCEAN: List[float] = []  # [i] : predictoor-profit
        self.trader_profits_USD: List[float] = []  # [i] : trader-profit

    @staticmethod
    def recent_metrics_names() -> List[str]:
        return AimodelMetrics.recent_metrics_names() + [
            "pdr_profit_OCEAN",
            "trader_profit_USD",
        ]

    def recent_metrics(
        self, extras: Optional[List[str]] = None
    ) -> List[Union[int, float]]:
        """Return most recent aimodel metrics + profit metrics"""
        rm = self.aim.recent_metrics().copy()
        rm.update(
            {
                "pdr_profit_OCEAN": self.pdr_profits_OCEAN[-1],
                "trader_profit_USD": self.trader_profits_USD[-1],
            }
        )

        if extras and "prob_up" in extras:
            rm["prob_up"] = self.probs_up_UP[-1] # FIXME: account for DOWN

        return rm

    @property
    def n_correct(self) -> int:
        return sum((p > 0.5) == t for p, t in zip(self.probs_up, self.ytrues))
