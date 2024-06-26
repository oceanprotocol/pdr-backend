from typing import Dict, List, Optional, Union

from enforce_typing import enforce_types
from pdr_backend.sim.constants import Dirn, UP, DOWN


@enforce_types
class ClassifMetrics(dict):
    def __init__(self):
        self[UP] = ClassifMetrics1Dir()
        self[DOWN] = ClassifMetrics1Dir()
        
    def update(self, classif_base: ClassifBaseData):
        self[UP].update(classif_base.UP.metrics())
        self[DOWN].update(classif_base.DOWN.metrics())

    @staticmethod
    def recent_metrics_names() -> List[str]:
        names = []
        names += self[UP].recent_metrics_names()
        names += self[DOWN].recent_metrics_names()
        return names

    @staticmethod
    def recent_metrics(self) -> Dict[str, float]:
        metrics = {}
        metrics.update(self[UP].recent_metrics())
        metrics.update(self[DOWN].recent_metrics())
        return metrics
    
@enforce_types
class ClassifMetrics1Dir:
    # pylint: disable=too-many-instance-attributes

    def __init__(self, dirn: Dirn):
        self.dirn = dirn
        
        # 'i' is iteration number i
        self.acc_ests: List[float] = []  # [i] : %-correct
        self.acc_ls: List[float] = []  # [i] : %-correct-lower
        self.acc_us: List[float] = []  # [i] : %-correct-upper

        self.f1s: List[float] = []  # [i] : f1-score
        self.precisions: List[float] = []  # [i] : precision
        self.recalls: List[float] = []  # [i] : recall

        self.losses: List[float] = []  # [i] : log-loss
        
    def update(self, metrics):
        acc_est, acc_l, acc_u, f1, precision, recall, loss = metrics
        
        self.acc_ests.append(acc_est)
        self.acc_ls.append(acc_l)
        self.acc_us.append(acc_u)

        self.f1s.append(f1)
        self.precisions.append(precision)
        self.recalls.append(recall)

        self.losses.append(loss)

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
        ]

    def recent_metrics(self) -> Dict[str, Union[int, float, None]]:
        """Return most recent aimodel metrics"""
        if not self.acc_ests:
            return {key: None for key in ClassifMetrics.recent_metrics_names()}

        dirn = self.dirn
        return {
            f"acc_est_{dirn}": self.acc_ests[-1],
            f"acc_l_{dirn}": self.acc_ls[-1],
            f"acc_u_{dirn}": self.acc_us[-1],
            f"f1_{dirn}": self.f1s[-1],
            f"precision_{dirn}": self.precisions[-1],
            f"recall_{dirn}": self.recalls[-1],
            f"loss_{dirn}": self.losses[-1],
        }

@enforce_types
class ClassifBaseData(dict):
    def __init__(self):
        self[UP] = ClassifBaseData1Dir()
        self[DOWN] = ClassifBaseData1Dir()

    def update(self, true_up_UP, prob_up_UP, sim_model_p: SimModelPrediction):
        self[UP].update(true_up_UP, sim_model_p.prob_up_UP)
        self[DOWN].update(true_up_DOWN, sim_model_p.prob_up_DOWN)
    
class ClassifBaseData1Dir:
    @enforce_types
    def __init__(self):
        # 'i' is iteration number i
        self.ytrues: List[bool] = []  # [i] : true value
        self.probs_up: List[float] = []  # [i] : model's pred. prob.

    @enforce_types
    def update(self, true_up: float, prob_up: float):
        self.ytrues.append(true_up)
        self.probs_up.append(prob_up)

    @property
    def ytrues_hat(self) -> List[bool]:
        """@return [i] : model pred. value"""
        return [p > 0.5 for p in self.probs_up]

    @property
    def n_correct(self) -> int:
        return sum(t == t_hat for t, t_hat in zip(self.ytrues, self.ytrues_hat))

    @property
    def n_trials(self) -> int:
        return len(self.ytrues)

    @enforce_types
    def accuracy(self) -> Tuple[float, float, float]:
        n_correct, n_trials = self.n_correct, self.n_trials
        acc_est = n_correct / n_trials
        acc_l, acc_u = proportion_confint(count=n_correct, nobs=n_trials)
        return (acc_est, acc_l, acc_u)

    @enforce_types
    def precision_recall_f1(self) -> Tuple[float, float, float]:
        (precision, recall, f1, _) = precision_recall_fscore_support(
            self.ytrues,
            self.ytrues_hat,
            average="binary",
            zero_division=0.0,
        )
        return (precision, recall, f1)

    @enforce_types
    def log_loss(self) -> float:
        if min(ytrues) == max(ytrues):
            return 3.0 # magic number
        return log_loss(self.ytrues, self.probs_up)

    @enforce_types
    def metrics(self) -> List[float]:
        return \
            list(self.accuracy()) + \
            list(precision_recall_f1) + \
            [self.log_loss()]


@enforce_types
class Profits:
    def __init__(self):
        self.pdr_profits_OCEAN: List[float] = []  # [i] : predictoor-profit
        self.trader_profits_USD: List[float] = []  # [i] : trader-profit
    
    def update_trader_profit(self, trader_profit_USD: float):
        self.trader_profits_USD.append(trader_profit_USD)

    def update_pdr_profit(
            self, others_stake, others_accuracy,
            stake_up, stake_down, true_up_close):
        others_stake_correct = others_stake * others_accuracy
        tot_stake = others_stake + stake_up + stake_down
        
        acct_up_profit = acct_down_profit = 0.0
        acct_up_profit -= stake_up
        acct_down_profit -= stake_down
        if true_up_close:
            tot_stake_correct = others_stake_correct + stake_up
            percent_to_me = stake_up / tot_stake_correct
            acct_up_profit += (revenue + tot_stake) * percent_to_me
        else:
            tot_stake_correct = others_stake_correct + stake_down
            percent_to_me = stake_down / tot_stake_correct
            acct_down_profit += (revenue + tot_stake) * percent_to_me
        pdr_profit_OCEAN = acct_up_profit + acct_down_profit
        
        self.pdr_profits_OCEAN.append(pdr_profit_OCEAN)
        
    @staticmethod
    def recent_metrics_names() -> List[str]:
        return ["pdr_profit_OCEAN", "trader_profit_USD"]
    
    @staticmethod
    def recent_metrics(self) -> Dict[str, float]:
        return {
            "pdr_profit_OCEAN" : self.pdr_profits_OCEAN[-1],
            "trader_profit_USD" : self.trader_profits_USD[-1],
        }
    
# pylint: disable=too-many-instance-attributes
@enforce_types
class SimState:
    def __init__(self):
        self.init_loop_attributes()

    def init_loop_attributes(self):
        self.iter_number = 0
        self.sim_model_data: Optional[SimModelData] = None
        self.sim_model: Optional[SimModel] = None
        self.classif_base = ClassifBaseData()
        self.classif_metrics = ClassifMetrics()
        self.profits = Profits()

    @staticmethod
    def recent_metrics_names() -> List[str]:
        return ClassifMetrics.recent_metrics_names() + \
            [
                "pdr_profit_OCEAN",
                "trader_profit_USD",
            ]

    def recent_metrics(
        self,
        extras: Optional[List[str]] = None
    ) -> List[Union[int, float]]:
        """Return most recent aimodel metrics + profit metrics"""
        metrics = self.metrics.recent_metrics().copy()
        metrics.update(
            {
                "pdr_profit_OCEAN": self.pdr_profits_OCEAN[-1],
                "trader_profit_USD": self.trader_profits_USD[-1],
            }
        )

        if extras and "prob_up" in extras:
            metrics["prob_up"] = self.probs_up_UP[-1] # FIXME: account for DOWN

        return metrics
