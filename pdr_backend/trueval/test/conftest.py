import os
from unittest.mock import Mock, patch

from pdr_backend.conftest_ganache import *  # pylint: disable=wildcard-import
from pdr_backend.models.feed import Feed
from pdr_backend.models.slot import Slot
from pdr_backend.trueval.trueval_config import TruevalConfig


@pytest.fixture()
def slot():
    feed = Feed(
        name="ETH-USDT",
        address="0xBE5449a6A97aD46c8558A3356267Ee5D2731ab5e",
        symbol="ETH-USDT",
        seconds_per_epoch=60,
        seconds_per_subscription=500,
        pair="eth-usdt",
        source="kraken",
        timeframe="5m",
        trueval_submit_timeout=100,
        owner="0xowner",
    )

    return Slot(
        feed=feed,
        slot_number=1692943200,
    )


@pytest.fixture(autouse=True)
def set_env_vars():
    original_value = os.environ.get("OWNER_ADDRS", None)
    os.environ["OWNER_ADDRS"] = "0xBE5449a6A97aD46c8558A3356267Ee5D2731ab5e"
    yield
    if original_value is not None:
        os.environ["OWNER_ADDRS"] = original_value
    else:
        os.environ.pop("OWNER_ADDRS", None)


@pytest.fixture()
def trueval_config():
    return TruevalConfig()


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
