from unittest.mock import Mock, patch
import pytest
from pdr_backend.dfbuyer.dfbuyer_agent import DFBuyerAgent
from pdr_backend.dfbuyer.dfbuyer_config import DFBuyerConfig
from pdr_backend.models.feed import Feed
from pdr_backend.util.constants import ZERO_ADDRESS  # pylint: disable=wildcard-import


def mock_feed():
    feed = Mock(spec=Feed)
    feed.name = "test feed"
    feed.seconds_per_epoch = 60
    return feed


@pytest.fixture
def dfbuyer_config():
    config = DFBuyerConfig()
    config.get_feeds = Mock()
    addresses = [ZERO_ADDRESS[: -len(str(i))] + str(i) for i in range(1, 7)]
    config.get_feeds.return_value = {address: mock_feed() for address in addresses}
    return config


@pytest.fixture
def mock_get_address():
    with patch("pdr_backend.dfbuyer.dfbuyer_agent.get_address") as mock:
        mock.return_value = ZERO_ADDRESS
        yield mock


@pytest.fixture
def mock_token():
    with patch("pdr_backend.dfbuyer.dfbuyer_agent.Token") as mock:
        yield mock


# pylint: disable=redefined-outer-name, unused-argument
@pytest.fixture
def dfbuyer_agent(mock_get_address, mock_token, dfbuyer_config):
    return DFBuyerAgent(dfbuyer_config)
