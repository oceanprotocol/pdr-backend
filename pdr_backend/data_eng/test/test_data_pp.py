from enforce_typing import enforce_types

from pdr_backend.data_eng.data_pp import DataPP
from pdr_backend.util.constants import CAND_TIMEFRAMES


@enforce_types
def test_data_pp_5m():
    # construct
    pp = _test_pp("5m")

    # test attributes
    assert pp.timeframe == "5m"
    assert pp.predict_feed_str == "kraken h ETH/USDT"
    assert pp.N_test == 2

    # test properties
    assert pp.timeframe_ms == 5 * 60 * 1000
    assert pp.timeframe_m == 5
    assert pp.predict_feed_tup == ("kraken", "high", "ETH-USDT")
    assert pp.exchange_str == "kraken"
    assert pp.signal_str == "high"
    assert pp.pair_str == "ETH-USDT"
    assert pp.base_str == "ETH"
    assert pp.quote_str == "USDT"


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
        predict_feed_str="kraken h ETH/USDT",
        N_test=2,
    )
    return pp
