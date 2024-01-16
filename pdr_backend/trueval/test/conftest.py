from unittest.mock import Mock, patch

from pdr_backend.conftest_ganache import *  # pylint: disable=wildcard-import
from pdr_backend.contract.slot import Slot
from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str
from pdr_backend.subgraph.subgraph_feed import mock_feed


@pytest.fixture()
def slot():
    feed = mock_feed("5m", "kraken", "ETH/USDT")
    return Slot(
        feed=feed,
        slot_number=1692943200,
    )


@pytest.fixture()
def mock_ppss(tmpdir):
    return PPSS(yaml_str=fast_test_yaml_str(tmpdir), network="development")


@pytest.fixture()
def predictoor_contract_mock():
    def mock_contract(*args, **kwarg):  # pylint: disable=unused-argument
        m = Mock()
        m.get_secondsPerEpoch.return_value = 60
        m.submit_trueval.return_value = {"tx": "0x123"}
        m.contract_address = "0x1"
        return m

    with patch(
        "pdr_backend.trueval.trueval_agent.PredictoorContract",
        return_value=mock_contract(),
    ) as mock_predictoor_contract_mock:
        yield mock_predictoor_contract_mock
