from typing import Dict, List, Optional, Tuple, Union

from enforce_typing import enforce_types
from sklearn.metrics import log_loss, precision_recall_fscore_support
from statsmodels.stats.proportion import proportion_confint

from pdr_backend.sim.constants import Dirn, dirn_str, UP, DOWN
from pdr_backend.sim.sim_model_prediction import SimModelPrediction

PERFS_NAMES = ["acc_est", "acc_l", "acc_u", "f1", "precision", "recall", "loss"]
    
class TrueVsPredVals:
    @enforce_types
    def __init__(self):
        # 'i' is iteration number i
        self.truevals: List[bool] = []  # [i] : true value
        self.predprobs: List[float] = []  # [i] : model's pred. prob.

    @enforce_types
    def update(self, trueval: bool, predprob: float):
        self.truevals.append(trueval)
        self.predprobs.append(predprob)

    @property
    def predvals(self) -> List[bool]:
        """@return [i] : model pred. value"""
        return [p > 0.5 for p in self.predprobs]

    @property
    def n_correct(self) -> int:
        return sum(tv == pv for tv, pv in zip(self.truevals, self.predvals))

    @property
    def n_trials(self) -> int:
        return len(self.truevals)

    @enforce_types
    def accuracy(self) -> Tuple[float, float, float]:
        n_correct, n_trials = self.n_correct, self.n_trials
        acc_est = n_correct / n_trials
        acc_l, acc_u = proportion_confint(count=n_correct, nobs=n_trials)
        return (acc_est, acc_l, acc_u)

    @enforce_types
    def precision_recall_f1(self) -> Tuple[float, float, float]:
        (precision, recall, f1, _) = precision_recall_fscore_support(
            self.truevals,
            self.predvals,
            average="binary",
            zero_division=0.0,
        )
        return (precision, recall, f1)

    @enforce_types
    def log_loss(self) -> float:
        if min(self.truevals) == max(self.truevals):
            return 3.0 # magic number
        return log_loss(self.truevals, self.predprobs)

    @enforce_types
    def perf_values(self) -> List[float]:
        perfs_list = \
            list(self.accuracy()) + \
            list(precision_recall_f1) + \
            [self.log_loss()]
        return perfs_list

@enforce_types
class ClassifBaseData(dict):
    def __init__(self):
        self[UP] = TrueVsPredVals()
        self[DOWN] = TrueVsPredVals()

    def update(
        self,
            
        # to establish UP model's accuracy: did next high go > prev close+% ?
        true_UP: bool,
            
        # to establish DOWN model's accuracy: did next low  go < prev close-% ?
        true_DOWN: bool,
            
        sim_model_p: SimModelPrediction,
    ):
        self[UP].update(true_UP, sim_model_p.prob_UP)
        self[DOWN].update(true_DOWN, sim_model_p.prob_DOWN)

@enforce_types
class HistPerfs1Dir:
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
        
    def update(self, perfs_list: list):
        """perfs_list typically comes from TrueVsPredVals.perf_values()"""
        acc_est, acc_l, acc_u, f1, precision, recall, loss = perfs_list
        
        self.acc_ests.append(acc_est)
        self.acc_ls.append(acc_l)
        self.acc_us.append(acc_u)

        self.f1s.append(f1)
        self.precisions.append(precision)
        self.recalls.append(recall)

        self.losses.append(loss)

    def recent_metrics_names(self) -> List[str]:
        s = dirn_str(self.dirn)
        return [
            f"acc_est_{s}",
            f"acc_l_{s}",
            f"acc_u_{s}",
            f"f1_{s}",
            f"precision_{s}",
            f"recall_{s}",
            f"loss_{s}",
        ]

    def recent_metrics_values(self) -> Dict[str, Union[int, float, None]]:
        """Return most recent aimodel metrics"""
        if not self.acc_ests:
            return {key: None for key in HistPerfs.recent_metrics_names()}

        s = dirn_str(self.dirn)
        return {
            f"acc_est_{s}": self.acc_ests[-1],
            f"acc_l_{s}": self.acc_ls[-1],
            f"acc_u_{s}": self.acc_us[-1],
            f"f1_{s}": self.f1s[-1],
            f"precision_{s}": self.precisions[-1],
            f"recall_{s}": self.recalls[-1],
            f"loss_{s}": self.losses[-1],
        }


@enforce_types
class HistPerfs(dict):
    def __init__(self):
        self[UP] = HistPerfs1Dir(UP)
        self[DOWN] = HistPerfs1Dir(DOWN)
        
    def update_recent(self, classif_base: ClassifBaseData):
        self[UP].update(classif_base.UP.recent_metrics_values())
        self[DOWN].update(classif_base.DOWN.recent_metrics_values())

    def recent_metrics_names(self) -> List[str]:
        names = []
        names += self[UP].recent_metrics_names()
        names += self[DOWN].recent_metrics_names()
        return names

    def recent_metrics_values(self) -> Dict[str, float]:
        metrics = {}
        metrics.update(self[UP].recent_metrics_values())
        metrics.update(self[DOWN].recent_metrics_values())
        return metrics
    

@enforce_types
class Profits:
    def __init__(self):
        self.pdr_profits_OCEAN: List[float] = []  # [i] : predictoor-profit
        self.trader_profits_USD: List[float] = []  # [i] : trader-profit

    @staticmethod
    def calc_pdr_profit(
        others_stake:float,
        others_accuracy: float,
        stake_up: float,
        stake_down: float,
        revenue: float,
        true_up_close: bool,
    ):
        assert others_stake >= 0
        assert 0.0 <= others_accuracy <= 1.0
        assert stake_up >= 0.0
        assert stake_down >= 0.0
        assert revenue >= 0.0
        
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
        return pdr_profit_OCEAN

    def update_pdr_profit(self, pdr_profit_OCEAN):
        self.pdr_profits_OCEAN.append(pdr_profit_OCEAN)
    
    def update_trader_profit(self, trader_profit_USD: float):
        self.trader_profits_USD.append(trader_profit_USD)
        
    def recent_metrics_names(self) -> List[str]:
        return ["pdr_profit_OCEAN", "trader_profit_USD"]
    
    def recent_metrics_values(self) -> Dict[str, float]:
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
        self.hist_perfs = HistPerfs()
        self.profits = Profits()

    def recent_metrics_names(self) -> List[str]:
        return self.hist_perfs.recent_metrics_names() + \
            self.profits.recent_metrics_names()

    def recent_metrics_values(self) -> List[Union[int, float]]:
        """Return most recent aimodel metrics + profit metrics"""
        metrics = {}
        metrics.update(self.hist_perfs.recent_metrics_values())
        metrics.update(self.profits.recent_metrics_values())
        return metrics
    
