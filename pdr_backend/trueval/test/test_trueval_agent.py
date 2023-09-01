from unittest.mock import patch, Mock, MagicMock
import pytest
from pdr_backend.trueval.trueval_agent import TruevalAgent
from pdr_backend.trueval.trueval_config import TruevalConfig
from pdr_backend.trueval.trueval_agent import get_trueval


def test_new_agent(trueval_config):
    agent = TruevalAgent(trueval_config, get_trueval)
    assert agent.config == trueval_config


def test_process_slot(agent, slot, predictoor_contract_mock):
    with patch.object(
        agent, "get_and_submit_trueval", return_value={"tx": "0x123"}
    ) as mock_submit:
        result = agent.process_slot(slot)
        assert result == {"tx": "0x123"}
        mock_submit.assert_called()


def test_get_contract_info_caching(agent, predictoor_contract_mock):
    agent.get_contract_info("0x1")
    agent.get_contract_info("0x1")
    assert predictoor_contract_mock.call_count == 1
    predictoor_contract_mock.assert_called_once_with(agent.config.web3_config, "0x1")


def test_submit_trueval_mocked_price_down(agent, slot, predictoor_contract_mock):
    with patch.object(agent, "get_trueval", return_value=(False, False)):
        result = agent.get_and_submit_trueval(
            slot, predictoor_contract_mock.return_value, 60
        )
        assert result == {"tx": "0x123"}
        predictoor_contract_mock.return_value.submit_trueval.assert_called_once_with(
            False, 1692943200, False, True
        )


def test_submit_trueval_mocked_price_up(agent, slot, predictoor_contract_mock):
    with patch.object(agent, "get_trueval", return_value=(True, False)):
        result = agent.get_and_submit_trueval(
            slot, predictoor_contract_mock.return_value, 60
        )
        assert result == {"tx": "0x123"}
        predictoor_contract_mock.return_value.submit_trueval.assert_called_once_with(
            True, 1692943200, False, True
        )


def test_submit_trueval_mocked_cancel(agent, slot, predictoor_contract_mock):
    with patch.object(agent, "get_trueval", return_value=(True, True)):
        result = agent.get_and_submit_trueval(
            slot, predictoor_contract_mock.return_value, 60
        )
        assert result == {"tx": "0x123"}
        predictoor_contract_mock.return_value.submit_trueval.assert_called_once_with(
            True, 1692943200, True, True
        )


def test_get_trueval_slot_up(agent, slot, predictoor_contract_mock):
    with patch.object(agent, "get_trueval", return_value=(True, True)):
        result = agent.get_trueval_slot(slot)
        assert result == (True, True)


def test_get_trueval_slot_down(agent, slot, predictoor_contract_mock):
    with patch.object(agent, "get_trueval", return_value=(False, True)):
        result = agent.get_trueval_slot(slot)
        assert result == (False, True)


def test_get_trueval_slot_cancel(agent, slot, predictoor_contract_mock):
    with patch.object(agent, "get_trueval", return_value=(True, False)):
        result = agent.get_trueval_slot(slot)
        assert result == (True, False)


def test_get_trueval_slot_too_many_requests_retry(agent, slot, predictoor_contract_mock):
    mock_get_trueval = MagicMock(
        side_effect=[Exception("Too many requests"), (True, True)]
    )
    with patch.object(agent, "get_trueval", mock_get_trueval), patch(
        "time.sleep", return_value=None
    ) as mock_sleep:
        result = agent.get_trueval_slot(slot)
        mock_sleep.assert_called_once_with(60)
        assert result == (True, True)
        assert mock_get_trueval.call_count == 2


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
def agent(trueval_config):
    return TruevalAgent(trueval_config, get_trueval)
