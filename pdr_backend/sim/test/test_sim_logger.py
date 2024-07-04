#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os
from unittest.mock import Mock

from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str
from pdr_backend.ppss.sim_ss import SimSS, sim_ss_test_dict
from pdr_backend.sim.sim_logger import SimLogLine
from pdr_backend.sim.sim_state import SimState
from pdr_backend.util.time_types import UnixTimeMs


@enforce_types
def test_sim_logger(tmpdir, caplog):
    s = fast_test_yaml_str(tmpdir)
    ppss = PPSS(yaml_str=s, network="development")

    log_dir = os.path.join(tmpdir, "logs")
    d = sim_ss_test_dict(log_dir, test_n=5)
    ppss.sim_ss = SimSS(d)

    st = Mock(spec=SimState)
    st.ytrues = [True, False, True, False, True]
    st.recent_metrics = Mock()
    st.recent_metrics.return_value = {
        "pdr_profit_OCEAN": 1.0,
        "trader_profit_USD": 2.0,
        "prob_up": 0.5,
        "acc_est": 0.6,
        "acc_l": 0.7,
        "acc_u": 0.8,
        "f1": 0.9,
        "precision": 0.1,
        "recall": 0.2,
        "loss": 0.3,
    }
    st.hist_profits = Mock()
    st.hist_profits.pdr_profits_OCEAN = [1.0, 2.0, 3.0, 4.0, 5.0]
    st.hist_profits.trader_profits_USD = [2.0, 3.0, 4.0, 5.0, 6.0]

    ut = UnixTimeMs(1701634400000)
    log_line = SimLogLine(ppss, st, 1, ut)
    log_line.log()
    assert "pdr_profit=" in caplog.text
    assert "tdr_profit=" in caplog.text
    assert f"Iter #2/{ppss.sim_ss.test_n}" in caplog.text

    log_line = SimLogLine(ppss, st, 1, ut)
    log_line.log()
    assert f"Iter #2/{ppss.sim_ss.test_n}" in caplog.text
