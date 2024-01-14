import os
import sys

from pdr_backend.subgraph.subgraph_feed import SubgraphFeed

# Add the root directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from pdr_backend.conftest_ganache import *  # pylint: disable=wildcard-import,wrong-import-position


@pytest.fixture(scope="session", autouse=True)
def set_test_env_var():
    previous = os.getenv("TEST")
    os.environ["TEST"] = "true"
    yield
    if previous is None:
        del os.environ["TEST"]
    else:
        os.environ["TEST"] = previous


@pytest.fixture(scope="session")
def mock_feeds():
    feeds = {
        "0x1": SubgraphFeed(
            "Feed: binance | BTC/USDT | 5m",
            "0x1",
            "BTC",
            100,
            300,
            "0xf",
            "BTC/USDT",
            "5m",
            "binance",
        )
    }
    return feeds


@pytest.fixture(scope="session")
def mock_predictoor_contract():
    mock_contract = Mock(spec=PredictoorContract)
    mock_contract.payout_multiple.return_value = None
    mock_contract.get_agg_predval.return_value = (12, 23)
    mock_contract.get_current_epoch.return_value = 100
    return mock_contract
