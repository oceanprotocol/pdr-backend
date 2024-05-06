import logging

import numpy as np
from enforce_typing import enforce_types

from pdr_backend.util.strutil import compactSmallNum

logger = logging.getLogger("sim_engine")


@enforce_types
# pylint: disable=too-many-instance-attributes
class SimLogLine:
    def __init__(self, ppss, st, test_i, ut, acct_up_profit, acct_down_profit):
        self.st = st

        self.test_n = ppss.sim_ss.test_n
        self.test_i = test_i
        self.ut = ut
        self.acct_up_profit = acct_up_profit
        self.acct_down_profit = acct_down_profit

        self.n_correct = sum(np.array(st.ytrues) == np.array(st.ytrues_hat))
        self.n_trials = len(st.ytrues)

        for key, item in st.recent_metrics(extras=["prob_up"]).items():
            setattr(self, key, item)

        # unused for now, but supports future configuration from ppss
        self.format = "compact"

    def log_line(self):
        s = f"Iter #{self.test_i+1}/{self.test_n}"
        s += f" ut={self.ut}"
        s += f" dt={self.ut.to_timestr()[:-7]}"
        s += " ║"

        s += f" prob_up={self.prob_up:.3f}"
        s += " pdr_profit="
        s += f"{compactSmallNum(self.acct_up_profit)} up"
        s += f" + {compactSmallNum(self.acct_down_profit)} down"
        s += f" = {compactSmallNum(self.pdr_profit_OCEAN)} OCEAN"
        s += f" (cumul {compactSmallNum(sum(self.st.pdr_profits_OCEAN))} OCEAN)"
        s += " ║"

        s += f" Acc={self.n_correct:4d}/{self.n_trials:4d} "
        s += f"= {self.acc_est*100:6.2f}% [{self.acc_l*100:5.1f}%, {self.acc_u*100:5.1f}%]"
        s += f" prcsn={self.precision:.3f} recall={self.recall:.3f}"
        s += f" f1={self.f1:.3f}"
        s += f" loss={self.loss:.3f}"
        s += " ║"

        s += f" tdr_profit=${self.trader_profit_USD:6.2f}"
        s += f" (cumul ${sum(self.st.trader_profits_USD):6.2f})"

        logger.info(s)
