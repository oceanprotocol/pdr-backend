import copy
import os

from enforce_typing import enforce_types

from pdr_backend.ppss.data_pp import DataPP
from pdr_backend.ppss.data_ss import DataSS
from pdr_backend.util.timeutil import timestr_to_ut

_D = {
    "input_feeds": ["kraken hc ETH/USDT", "binanceus h ETH/USDT,TRX/DAI"],
    "csv_dir": "csvs",
    "st_timestr": "2023-06-18",
    "fin_timestr": "2023-06-21",
    "max_n_train": 7,
    "autoregressive_n": 3,
}


@enforce_types
def test_data_ss_basic():
    ss = DataSS(_D)

    # yaml properties
    assert ss.input_feeds_strs == ["kraken hc ETH/USDT", "binanceus h ETH/USDT,TRX/DAI"]
    assert "csvs" in ss.csv_dir
    assert ss.st_timestr == "2023-06-18"
    assert ss.fin_timestr == "2023-06-21"

    assert ss.max_n_train == 7
    assert ss.autoregressive_n == 3

    assert sorted(ss.exchs_dict.keys()) == ["binanceus", "kraken"]

    # derivative properties
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
    assert "DataSS" in str(ss)


@enforce_types
def test_data_ss_now():
    d = copy.deepcopy(_D)
    d["fin_timestr"] = "now"
    ss = DataSS(d)

    assert ss.fin_timestr == "now"
    assert ss.fin_timestamp == timestr_to_ut("now")


@enforce_types
def test_csv_dir(tmpdir):
    # rel path given; needs an abs path
    d = copy.deepcopy(_D)
    d["csv_dir"] = "csvs"
    ss = DataSS(d)
    target_csv_dir = os.path.abspath("csvs")
    assert ss.csv_dir == target_csv_dir

    # abs path given
    d = copy.deepcopy(_D)
    d["csv_dir"] = os.path.join(tmpdir, "csvs")
    ss = DataSS(d)
    target_csv_dir = os.path.join(tmpdir, "csvs")
    assert ss.csv_dir == target_csv_dir


@enforce_types
def test_data_ss_copy():
    ss = DataSS(_D)
    assert ss.n_input_feeds == 4

    # copy 1: don't need to append the new feed
    pp = DataPP(
        {
            "timeframe": "5m",
            "predict_feeds": ["kraken h ETH/USDT"],
            "sim_only": {"test_n": 2},
        }
    )
    ss2 = ss.copy_with_yval(pp)
    assert ss2.n_input_feeds == 4 + 0

    # copy 2: do need to append the new feed
    pp = DataPP(
        {
            "timeframe": "5m",
            "predict_feeds": ["binanceus c TRX/USDC"],
            "sim_only": {"test_n": 2},
        }
    )
    ss3 = ss.copy_with_yval(pp)
    assert ss3.n_input_feeds == 4 + 1
