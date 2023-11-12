from enforce_typing import enforce_types

from pdr_backend.data_eng.data_pp import DataPP
from pdr_backend.data_eng.data_ss import DataSS, _list_with
from pdr_backend.util.timeutil import timestr_to_ut


@enforce_types
def test_data_ss_basic(tmpdir):
    ss = DataSS(
        csv_dir=str(tmpdir),
        st_timestamp=timestr_to_ut("2023-06-18"),
        fin_timestamp=timestr_to_ut("2023-06-21"),
        max_N_train=7,
        Nt=3,
        signals=["high", "close"],
        coins=["ETH", "BTC", "TRX"],
        exchange_ids=["kraken", "binanceus"],
    )

    # test attributes
    assert ss.csv_dir == str(tmpdir)
    assert ss.st_timestamp == timestr_to_ut("2023-06-18")
    assert ss.fin_timestamp == timestr_to_ut("2023-06-21")

    assert ss.max_N_train == 7
    assert ss.Nt == 3

    assert ss.signals == ["high", "close"]
    assert ss.coins == ["ETH", "BTC", "TRX"]

    assert sorted(ss.exchs_dict.keys()) == ["binanceus", "kraken"]

    # test properties
    assert ss.n == 2 * 3 * 2 * 3
    assert ss.n_exchs == 2
    assert len(ss.exchange_ids) == 2
    assert "binanceus" in ss.exchange_ids
    assert ss.n_signals == 2
    assert ss.n_coins == 3

    # test str
    assert "DataSS=" in str(ss)


@enforce_types
def test_data_ss_copy(tmpdir):
    ss = DataSS(
        csv_dir=str(tmpdir),
        st_timestamp=timestr_to_ut("2023-06-18"),
        fin_timestamp=timestr_to_ut("now"),
        max_N_train=7,
        Nt=3,
        signals=["high"],
        coins=["ETH", "BTC"],
        exchange_ids=["kraken"],
    )

    # copy 1: don't need to append lists
    pp = DataPP(
        timeframe="5m",
        yval_exchange_id="kraken",
        yval_coin="ETH",
        usdcoin="USDT",
        yval_signal="high",
        N_test=2,
    )
    ss2 = ss.copy_with_yval(pp)
    assert ss2.signals == ["high"]
    assert sorted(ss2.coins) == sorted(["ETH", "BTC"])  # no order guarantee
    assert ss2.exchange_ids == ["kraken"]

    # copy 2: need to append all three lists
    pp = DataPP(
        timeframe="5m",
        yval_exchange_id="binanceus",
        yval_coin="TRX",
        usdcoin="USDC",
        yval_signal="close",
        N_test=2,
    )
    ss3 = ss.copy_with_yval(pp)
    assert sorted(ss3.signals) == sorted(["high", "close"])  # no order guarantee
    assert sorted(ss3.coins) == sorted(["ETH", "BTC", "TRX"])  # ""
    assert sorted(ss3.exchange_ids) == sorted(["kraken", "binanceus"])  # ""


@enforce_types
def test_list_with():
    assert _list_with([], 2) == [2]
    assert _list_with([1, 2, 10], 2) == [1, 2, 10]
    assert _list_with([1, 2, 10], 5) == [1, 2, 10, 5]

    assert _list_with([], "foo") == ["foo"]
    assert _list_with(["a", 3.0, None, 77], "bb") == ["a", 3.0, None, 77, "bb"]
