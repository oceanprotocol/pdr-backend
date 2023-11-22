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
    return feed


@enforce_types
def mock_ppss(predictoor_contract, tmpdir):
    yaml_str = fast_test_yaml_str(tmpdir)
    ppss = PPSS("barge-pytest", yaml_str=yaml_str)

    ppss.data_pp.set_timeframe("5m")
    ppss.data_pp.set_predict_feeds(["mexc c BTC/USDT"])

    ppss.web3_pp.get_feeds = Mock()
    ppss.web3_pp.get_feeds.return_value = {
        "0x0000000000000000000000000000000000000000": mock_feed()
    }
    ppss.web3_pp.get_contracts = Mock()
    ppss.web3_pp.get_contracts.return_value = {
        "0x0000000000000000000000000000000000000000": predictoor_contract
    }

    ppss.trader_ss.set_max_tries(10)
    ppss.trader_ss.set_position_size(10.0)
    ppss.trader_ss.set_min_buffer(20)

    return ppss


@enforce_types
def run_no_feeds(tmpdir, agent_class):
    yaml_str = fast_test_yaml_str(tmpdir)
    ppss = PPSS("barge-pytest", yaml_str=yaml_str)
    ppss.data_pp.set_predict_feeds([])
    ppss.web3_pp.get_feeds = Mock()
    ppss.web3_pp.get_feeds.return_value = {}

    with pytest.raises(ValueError):
        agent_class(ppss)
