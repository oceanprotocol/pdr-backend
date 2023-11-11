from enforce_typing import enforce_types

from pdr_backend.data_eng.data_ss import DataSS
from pdr_backend.util.timeutil import timestr_to_ut


@enforce_types
def test_data_ss_5m(tmpdir):
    ss = DataSS(
        csv_dir=str(tmpdir),
        st_timestamp=timestr_to_ut("2023-06-18"),
        fin_timestamp=timestr_to_ut("2023-06-21"),
        max_N_train=7,
        Nt=3,
        signals=["high", "close"],
        coins=["ETH", "BTC", "TRX"],
        exchange_ids=["kraken", "binance"],
    )

    # test attributes
    assert ss.csv_dir == str(tmpdir)
    assert ss.st_timestamp == timestr_to_ut("2023-06-18")
    assert ss.fin_timestamp == timestr_to_ut("2023-06-21")

    assert ss.max_N_train == 7
    assert ss.Nt == 3

    assert ss.signals == ["high", "close"]
    assert ss.coins == ["ETH", "BTC", "TRX"]

    assert sorted(ss.exchs_dict.keys()) == ["binance", "kraken"]

    # test properties
    assert ss.n == 2 * 3 * 2 * 3
    assert ss.n_exchs == 2
    assert len(ss.exchange_ids) == 2
    assert "binance" in ss.exchange_ids
    assert ss.n_signals == 2
    assert ss.n_coins == 3

    # test str
    assert "DataSS=" in str(ss)
