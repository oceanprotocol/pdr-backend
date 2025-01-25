import os
from unittest.mock import Mock

from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str
from pdr_backend.ppss.sim_ss import SimSS, sim_ss_test_dict
from pdr_backend.sim.sim_logger import SimLogLine
from pdr_backend.sim.sim_state import SimState
from pdr_backend.util.time_types import UnixTimeMs


def test_compact_num(tmpdir, caplog):
    s = fast_test_yaml_str(tmpdir)
    ppss = PPSS(yaml_str=s, network="development")

    log_dir = os.path.join(tmpdir, "logs")
    d = sim_ss_test_dict(log_dir, test_n=5)
    ppss.sim_ss = SimSS(d)

    st = Mock(spec=SimState)
    st.ytrues = [True, False, True, False, True]
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
    st.pdr_profits_OCEAN = [1.0, 2.0, 3.0, 4.0, 5.0]
    st.trader_profits_USD = [2.0, 3.0, 4.0, 5.0, 6.0]

    ut = UnixTimeMs(1701634400000)
    log_line = SimLogLine(ppss, st, 1, ut, 0.5, 0.6)
    log_line.log_line()

    assert "pdr_profit=0.50 up" in caplog.text
    assert "prcsn=0.100" in caplog.text
    assert f"Iter #2/{ppss.sim_ss.test_n}" in caplog.text

    log_line = SimLogLine(ppss, st, 1, ut, 0.003, 0.4)
    log_line.log_line()

    assert "pdr_profit=3.00e-3 up" in caplog.text
    assert "prcsn=0.100" in caplog.text
    assert f"Iter #2/{ppss.sim_ss.test_n}" in caplog.text
