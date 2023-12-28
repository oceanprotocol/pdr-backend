import os

from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str, mock_feed_ppss, mock_ppss
from pdr_backend.ppss.web3_pp import del_network_override


@enforce_types
def test_ppss_from_file(tmpdir):
    yaml_str = fast_test_yaml_str(tmpdir)
    yaml_filename = os.path.join(tmpdir, "ppss.yaml")
    with open(yaml_filename, "a") as f:
        f.write(yaml_str)

    _test_ppss(yaml_filename=yaml_filename, network="development")


@enforce_types
def test_ppss_from_str(tmpdir):
    yaml_str = fast_test_yaml_str(tmpdir)
    _test_ppss(yaml_str=yaml_str, network="development")


@enforce_types
def _test_ppss(yaml_filename=None, yaml_str=None, network=None):
    # construct
    ppss = PPSS(yaml_filename, yaml_str, network)

    # yaml properties - test lightly, since each *_pp and *_ss has its tests
    #  - so just do one test for each of this class's pp/ss attribute
    assert ppss.trader_ss.timeframe in ["5m", "1h"]
    assert isinstance(ppss.lake_ss.st_timestr, str)
    assert ppss.dfbuyer_ss.weekly_spending_limit >= 0
    assert ppss.predictoor_ss.aimodel_ss.approach == "LIN"
    assert ppss.payout_ss.batch_size >= 0
    assert 1 <= ppss.predictoor_ss.s_until_epoch_end <= 120
    assert isinstance(ppss.sim_ss.do_plot, bool)
    assert 0.0 <= ppss.trader_pp.fee_percent <= 0.99
    assert "USD" in ppss.trader_ss.buy_amt_str
    assert ppss.trueval_ss.batch_size >= 0
    assert isinstance(ppss.web3_pp.address_file, str)

    # str
    s = str(ppss)
    assert "lake_ss" in s
    assert "dfbuyer_ss" in s
    assert "payout_ss" in s
    assert "predictoor_ss" in s
    assert "sim_ss" in s
    assert "trader_pp" in s
    assert "trader_ss" in s
    assert "trueval_ss" in s
    assert "web3_pp" in s


@enforce_types
def test_mock_feed_ppss(monkeypatch):
    del_network_override(monkeypatch)

    feed, ppss = mock_feed_ppss("5m", "binance", "BTC/USDT", "sapphire-mainnet")

    assert feed.timeframe == "5m"
    assert feed.source == "binance"
    assert feed.pair == "BTC/USDT"

    assert ppss.predictoor_ss.timeframe == "5m"
    assert str(ppss.predictoor_ss.predict_feed) == "binance BTC/USDT c 5m"
    assert ppss.lake_ss.input_feeds_strs == ["binance BTC/USDT c 5m"]
    assert ppss.web3_pp.network == "sapphire-mainnet"


@enforce_types
def test_mock_ppss(monkeypatch):
    del_network_override(monkeypatch)
    ppss = mock_ppss(["binance BTC/USDT c 5m"], "sapphire-mainnet")
    assert ppss.predictoor_ss.timeframe == "5m"
    assert str(ppss.predictoor_ss.predict_feed) == "binance BTC/USDT c 5m"
    assert ppss.lake_ss.input_feeds_strs == ["binance BTC/USDT c 5m"]
    assert ppss.web3_pp.network == "sapphire-mainnet"


@enforce_types
def test_mock_ppss_default_network_development(monkeypatch):
    del_network_override(monkeypatch)
    ppss = mock_ppss(["binance BTC/USDT c 5m"])
    assert ppss.web3_pp.network == "development"
