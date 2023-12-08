from unittest.mock import Mock

from enforce_typing import enforce_types
import pytest

from pdr_backend.models.feed import Feed
from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str


@enforce_types
def mock_feed():
    feed = Mock(spec=Feed)
    feed.name = "test feed"
    feed.address = "0xtestfeed"
    feed.seconds_per_epoch = 60
    feed.source = "binance"
    feed.pair = "BTC/USDT"
    return feed


@enforce_types
def mock_ppss():
    yaml_str = fast_test_yaml_str(tmpdir=None)
    ppss = PPSS(yaml_str=yaml_str, network="development")

    ppss.data_pp.set_timeframe("5m")
    ppss.data_pp.set_predict_feeds(["binance c BTC/USDT"])

    ppss.trader_ss.set_max_tries(10)
    ppss.trader_ss.set_position_size(10.0)
    ppss.trader_ss.set_min_buffer(20)

    return ppss


@enforce_types
def run_no_feeds(agent_class):
    yaml_str = fast_test_yaml_str()
    ppss = PPSS(yaml_str=yaml_str, network="development")
    ppss.data_pp.set_predict_feeds([])

    with pytest.raises(ValueError):
        agent_class(ppss)
