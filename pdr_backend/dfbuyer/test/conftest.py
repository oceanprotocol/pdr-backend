from unittest.mock import MagicMock, Mock, patch
import pytest

from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str
from pdr_backend.dfbuyer.dfbuyer_agent import DFBuyerAgent
from pdr_backend.models.feed import Feed
from pdr_backend.util.constants import (
    MAX_UINT,
    ZERO_ADDRESS,
)  # pylint: disable=wildcard-import


def mock_feed():
    feed = Mock(spec=Feed)
    feed.name = "test feed"
    feed.seconds_per_epoch = 60
    return feed


@pytest.fixture()
def mock_token():
    with patch("pdr_backend.dfbuyer.dfbuyer_agent.Token") as mock_token_class:
        mock_token_instance = MagicMock()
        mock_token_instance.allowance.return_value = MAX_UINT
        mock_token_class.return_value = mock_token_instance
        yield mock_token_class


@pytest.fixture
def dfbuyer_config(tmpdir):
    yaml_str = fast_test_yaml_str(tmpdir)
    ppss = PPSS(yaml_str=yaml_str, network="development")

    ppss.web3_pp.get_feeds = Mock()
    addresses = [ZERO_ADDRESS[: -len(str(i))] + str(i) for i in range(1, 7)]
    ppss.web3_pp.get_feeds.return_value = {
        address: mock_feed() for address in addresses
    }
    return ppss


@pytest.fixture
def mock_get_address():
    with patch("pdr_backend.dfbuyer.dfbuyer_agent.get_address") as mock:
        mock.return_value = ZERO_ADDRESS
        yield mock


# pylint: disable=redefined-outer-name, unused-argument
@pytest.fixture
def dfbuyer_agent(mock_get_address, mock_token, dfbuyer_config):
    return DFBuyerAgent(dfbuyer_config)
