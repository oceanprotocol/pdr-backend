import logging

import numpy as np
from enforce_typing import enforce_types

from pdr_backend.util.strutil import compactSmallNum

logger = logging.getLogger("sim_engine")


@enforce_types
class SimLogLine:
    def __init__(self, ppss, st, test_i, ut):
        self.st = st
        self.test_n = ppss.sim_ss.test_n
        self.test_i = test_i
        self.ut = ut

    def log(self):
        s = f"Iter #{self.test_i+1}/{self.test_n}"
        s += f" ut={self.ut}"
        s += f" dt={self.ut.to_timestr()[:-7]}"
        s += " ║"

        pdr_profits = self.st.hist_profits.pdr_profits_OCEAN
        s += f"pdr_profit={compactSmallNum(pdr_profits[-1])} OCEAN"
        s += f" (cumul {compactSmallNum(sum(pdr_profits))} OCEAN)"
        s += " ║"

        trader_profits = self.st.hist_profits.trader_profits_USD
        s += f" tdr_profit=${trader_profits[-1]:6.2f}"
        s += f" (cumul ${sum(trader_profits):6.2f})"

        logger.info(s)
