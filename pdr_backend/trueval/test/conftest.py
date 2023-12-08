from unittest.mock import Mock, patch

from pdr_backend.conftest_ganache import *  # pylint: disable=wildcard-import
from pdr_backend.models.feed import Feed
from pdr_backend.models.slot import Slot
from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str


@pytest.fixture()
def slot():
    feed = Feed(
        name="ETH-USDT",
        address="0xBE5449a6A97aD46c8558A3356267Ee5D2731ab5e",
        symbol="ETH-USDT",
        seconds_per_subscription=500,
        trueval_submit_timeout=100,
        owner="0xowner",
        pair="eth-usdt",
        source="kraken",
        timeframe="5m",
    )

    return Slot(
        feed=feed,
        slot_number=1692943200,
    )


@pytest.fixture()
def mock_ppss(tmpdir):
    return PPSS(yaml_str=fast_test_yaml_str(tmpdir), network="development")


@pytest.fixture()
def predictoor_contract_mock():
    with patch(
        "pdr_backend.trueval.trueval_agent_base.PredictoorContract",
        return_value=mock_contract(),
    ) as mock_predictoor_contract_mock:
        yield mock_predictoor_contract_mock


def mock_contract(*args, **kwarg):  # pylint: disable=unused-argument
    m = Mock()
    m.get_secondsPerEpoch.return_value = 60
    m.submit_trueval.return_value = {"tx": "0x123"}
    m.contract_address = "0x1"
    return m
