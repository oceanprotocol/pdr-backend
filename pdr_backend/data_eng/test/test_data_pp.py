from enforce_typing import enforce_types

from pdr_backend.data_eng.constants import CAND_TIMEFRAMES
from pdr_backend.data_eng.data_pp import DataPP


@enforce_types
def test_data_pp_5m():
    # construct
    pp = _test_pp("5m")

    # test attributes
    assert pp.timeframe == "5m"
    assert pp.yval_exchange_id == "kraken"
    assert pp.yval_coin == "ETH"
    assert pp.usdcoin == "USDT"
    assert pp.yval_signal == "high"
    assert pp.N_test == 2

    # test properties
    assert pp.timeframe_ms == 5 * 60 * 1000
    assert pp.timeframe_m == 5


@enforce_types
def test_data_pp_1h():
    ss = _test_pp("1h")

    assert ss.timeframe == "1h"
    assert ss.timeframe_ms == 60 * 60 * 1000
    assert ss.timeframe_m == 60


@enforce_types
def _test_pp(timeframe: str) -> DataPP:
    assert timeframe in CAND_TIMEFRAMES
    pp = DataPP(
        timeframe=timeframe,
        yval_exchange_id="kraken",
        yval_coin="ETH",
        usdcoin="USDT",
        yval_signal="high",
        N_test=2,
    )
    return pp
