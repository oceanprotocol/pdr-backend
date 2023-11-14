from enforce_typing import enforce_types

from pdr_backend.data_eng.data_pp import DataPP
from pdr_backend.data_eng.data_ss import DataSS
from pdr_backend.util.timeutil import timestr_to_ut


@enforce_types
def test_data_ss_basic(tmpdir):
    ss = DataSS(
        ["kraken hc ETH/USDT", "binanceus h ETH/USDT,TRX/DAI"],
        csv_dir=str(tmpdir),
        st_timestr="2023-06-18",
        fin_timestr="2023-06-21",
        max_n_train=7,
        autoregressive_n=3,
    )

    # test attributes
    assert ss.input_feeds_strs == ["kraken hc ETH/USDT", "binanceus h ETH/USDT,TRX/DAI"]
    assert ss.csv_dir == str(tmpdir)
    assert ss.st_timestr == "2023-06-18"
    assert ss.fin_timestr == "2023-06-21"

    assert ss.max_n_train == 7
    assert ss.autoregressive_n == 3

    assert sorted(ss.exchs_dict.keys()) == ["binanceus", "kraken"]

    # test properties
    assert ss.st_timestamp == timestr_to_ut("2023-06-18")
    assert ss.fin_timestamp == timestr_to_ut("2023-06-21")
    assert ss.input_feed_tups == [
        ("kraken", "high", "ETH-USDT"),
        ("kraken", "close", "ETH-USDT"),
        ("binanceus", "high", "ETH-USDT"),
        ("binanceus", "high", "TRX-DAI"),
    ]
    assert ss.exchange_pair_tups == set(
        [
            ("kraken", "ETH-USDT"),
            ("binanceus", "ETH-USDT"),
            ("binanceus", "TRX-DAI"),
        ]
    )
    assert len(ss.input_feed_tups) == ss.n_input_feeds == 4
    assert ss.n == 4 * 3 == 12
    assert ss.n_exchs == 2
    assert len(ss.exchange_strs) == 2
    assert "binanceus" in ss.exchange_strs

    # test str
    assert "DataSS=" in str(ss)


@enforce_types
def test_data_ss_now(tmpdir):
    ss = DataSS(
        ["kraken h ETH/USDT"],
        csv_dir=str(tmpdir),
        st_timestr="2023-06-18",
        fin_timestr="now",
        max_n_train=7,
        autoregressive_n=3,
    )
    assert ss.fin_timestr == "now"
    assert ss.fin_timestamp == timestr_to_ut("now")


@enforce_types
def test_data_ss_copy(tmpdir):
    ss = DataSS(
        ["kraken h ETH/USDT BTC/USDT"],
        csv_dir=str(tmpdir),
        st_timestr="2023-06-18",
        fin_timestr="now",
        max_n_train=7,
        autoregressive_n=3,
    )

    # copy 1: don't need to append the new feed
    pp = DataPP(
        "5m",
        "kraken h ETH/USDT",
        test_n=2,
    )
    ss2 = ss.copy_with_yval(pp)
    assert ss2.n_input_feeds == 2

    # copy 2: do need to append the new feed
    pp = DataPP(
        "5m",
        "binanceus c TRX/USDC",
        test_n=2,
    )
    ss3 = ss.copy_with_yval(pp)
    assert ss3.n_input_feeds == 3
