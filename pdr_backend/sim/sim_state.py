from typing import Dict, List, Optional, Tuple, Union

from enforce_typing import enforce_types

from pdr_backend.aimodel.true_vs_pred import PERF_NAMES, TrueVsPred
from pdr_backend.sim.constants import Dirn, dirn_str, UP, DOWN


#=============================================================================
# HistPerfs

@enforce_types
class HistPerfs:
    """Historical performances, for 1 model dir'n (eg UP)"""
    
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
        """perfs_list typically comes from TrueVsPred.perf_values()"""
        acc_est, acc_l, acc_u, f1, precision, recall, loss = perfs_list
        
        self.acc_ests.append(acc_est)
        self.acc_ls.append(acc_l)
        self.acc_us.append(acc_u)

        self.f1s.append(f1)
        self.precisions.append(precision)
        self.recalls.append(recall)

        self.losses.append(loss)

    def metrics_names(self) -> List[str]:
        """@return e.g. ['acc_est_UP', 'acc_l_UP', ..., 'loss_UP]"""
        return [f"{name}_{dirn_str(self.dirn)}"
                for name in PERF_NAMES]
    
    def recent_metrics_values(self) -> Dict[str, Union[int, float, None]]:
        """Return most recent aimodel metrics"""
        if not self.acc_ests:
            return {name: None for name in self.metrics_names()}

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
    
#=============================================================================
# HistProfits

PROFIT_NAMES = ["pdr_profit_OCEAN", "trader_profit_USD"]

@enforce_types
class HistProfits:
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
        
        amt_sent = stake_up + stake_down
        others_stake_correct = others_stake * others_accuracy
        tot_stake = others_stake + stake_up + stake_down
        if true_up_close:
            tot_stake_correct = others_stake_correct + stake_up
            percent_to_me = stake_up / tot_stake_correct
            amt_received = (revenue + tot_stake) * percent_to_me
        else:
            tot_stake_correct = others_stake_correct + stake_down
            percent_to_me = stake_down / tot_stake_correct
            amt_received = (revenue + tot_stake) * percent_to_me
        pdr_profit_OCEAN = amt_received - amt_sent
        return pdr_profit_OCEAN

    def update(self, pdr_profit_OCEAN: float, trader_profit_USD: float):
        self.pdr_profits_OCEAN.append(pdr_profit_OCEAN)
        self.trader_profits_USD.append(trader_profit_USD)
        
    def metrics_names(self) -> List[str]:
        return PROFIT_NAMES
    
    def recent_metrics_values(self) -> Dict[str, float]:
        if not self.pdr_profits_OCEAN:
            return {name: None for name in self.metrics_names()}
        
        return {
            "pdr_profit_OCEAN" : self.pdr_profits_OCEAN[-1],
            "trader_profit_USD" : self.trader_profits_USD[-1],
        }

#=============================================================================
# SimState

@enforce_types
class SimState:
    def __init__(self):
        self.init_loop_attributes()

    def init_loop_attributes(self):
        self.iter_number = 0
        self.sim_model_data: Optional[SimModelData] = None
        self.sim_model: Optional[SimModel] = None
        self.true_vs_pred = {UP: TrueVsPred(), DOWN: TrueVsPred()}
        self.hist_perfs = {UP: HistPerfs(UP), DOWN: HistPerfs(DOWN)}
        self.hist_profits = HistProfits()

    def update(
        self,
        trueval: dict,
        predprob: dict,
        pdr_profit_OCEAN: float,
        trader_profit_USD: float,
    ):
        """
        @arguments
          trueval -- dict of {UP: trueval_UP, DOWN: trueval_DOWN}
          predprob -- dict of {UP: predprob_UP, DOWN: predprob_DOWN}
          pdr_profit_OCEAN --
          trader_profit_USD --
        """
        self.true_vs_pred[UP].update(trueval[UP], predprob[UP])
        self.true_vs_pred[DOWN].update(trueval[DOWN], predprob[DOWN])

        self.hist_perfs[UP].update(self.true_vs_pred[UP].perf_values())
        self.hist_perfs[DOWN].update(self.true_vs_pred[DOWN].perf_values())
        
        self.hist_profits.update(pdr_profit_OCEAN, trader_profit_USD)
        
    def metrics_names(self) -> List[str]:
        return self.hist_perfs[UP].metrics_names() + \
            self.hist_perfs[DOWN].metrics_names() + \
            self.hist_profits.metrics_names()

    def recent_metrics_values(self) -> List[Union[int, float]]:
        """Return most recent aimodel metrics + profit metrics"""
        metrics = {}
        metrics.update(self.hist_perfs[UP].recent_metrics_values())
        metrics.update(self.hist_perfs[DOWN].recent_metrics_values())
        metrics.update(self.hist_profits.recent_metrics_values())
        return metrics
    
