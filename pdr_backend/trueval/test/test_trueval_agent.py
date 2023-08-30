from unittest.mock import patch, Mock, MagicMock
import pytest
from pdr_backend.trueval.trueval_agent import TruevalAgent
from pdr_backend.trueval.trueval_config import TruevalConfig
from pdr_backend.trueval.main import get_true_val


def test_new_agent(trueval_config):
    agent = TruevalAgent(trueval_config, get_true_val)
    assert agent.config == trueval_config


def test_process_slot(agent, slot, predictoor_contract):
    with patch.object(
        agent, "get_and_submit_trueval", return_value={"tx": "0x123"}
    ) as mock_submit:
        result = agent.process_slot(slot)
        assert result == {"tx": "0x123"}
        mock_submit.assert_called()


def test_get_contract_info_caching(agent, predictoor_contract):
    agent.get_contract_info("0x1")
    agent.get_contract_info("0x1")
    assert predictoor_contract.call_count == 1
    predictoor_contract.assert_called_once_with(agent.config.web3_config, "0x1")


def test_submit_trueval_mocked_price_down(agent, slot, predictoor_contract):
    with patch("ccxt.kraken.fetch_ohlcv", mock_fetch_ohlcv_down):
        result = agent.get_and_submit_trueval(
            slot, predictoor_contract.return_value, 60
        )
        assert result == {"tx": "0x123"}
        predictoor_contract.return_value.submit_trueval.assert_called_once_with(
            False, 1692943200, False, True
        )


def test_submit_trueval_mocked_price_up(agent, slot, predictoor_contract):
    with patch("ccxt.kraken.fetch_ohlcv", mock_fetch_ohlcv_up):
        result = agent.get_and_submit_trueval(
            slot, predictoor_contract.return_value, 60
        )
        assert result == {"tx": "0x123"}
        predictoor_contract.return_value.submit_trueval.assert_called_once_with(
            True, 1692943200, False, True
        )


def test_take_step(slot, agent):
    mocked_env = {
        "SLEEP_TIME": "1",
        "BATCH_SIZE": "1",
    }

    mocked_web3_config = MagicMock()

    with patch.dict("os.environ", mocked_env), patch.object(
        agent.config, "web3_config", new=mocked_web3_config
    ), patch("time.sleep"), patch.object(
        TruevalConfig, "get_pending_slots", return_value=[slot]
    ), patch.object(
        TruevalAgent, "process_slot"
    ) as ps_mock:
        agent.take_step()

    ps_mock.assert_called_once_with(slot)


def test_run(slot, agent):
    mocked_env = {
        "SLEEP_TIME": "1",
        "BATCH_SIZE": "1",
    }

    mocked_web3_config = MagicMock()

    with patch.dict("os.environ", mocked_env), patch.object(
        agent.config, "web3_config", new=mocked_web3_config
    ), patch("time.sleep"), patch.object(
        TruevalConfig, "get_pending_slots", return_value=[slot]
    ), patch.object(
        TruevalAgent, "process_slot"
    ) as ps_mock:
        agent.run(True)

    ps_mock.assert_called_once_with(slot)


# ----------------------------------------------
# Fixtures


@pytest.fixture()
def trueval_config():
    return TruevalConfig()


@pytest.fixture()
def agent(trueval_config):
    return TruevalAgent(trueval_config, get_true_val)


@pytest.fixture()
def predictoor_contract():
    with patch(
        "pdr_backend.trueval.trueval_agent.PredictoorContract",
        return_value=mock_contract(),
    ) as mock_predictoor_contract:
        yield mock_predictoor_contract


# ----------------------------------------------
### Mocks


def mock_contract(*args, **kwarg):
    m = Mock()
    m.get_secondsPerEpoch.return_value = 60
    m.submit_trueval.return_value = {"tx": "0x123"}
    m.contract_address = "0x1"
    return m


def mock_fetch_ohlcv_down(*args, **kwargs):
    since = kwargs.get("since")
    if since == 1692943140:
        return [[None, 200]]
    elif since == 1692943200:
        return [[None, 100]]
    else:
        raise ValueError("Invalid timestamp")


def mock_fetch_ohlcv_up(*args, **kwargs):
    since = kwargs.get("since")
    if since == 1692943140:
        return [[None, 100]]
    elif since == 1692943200:
        return [[None, 200]]
    else:
        raise ValueError("Invalid timestamp")
