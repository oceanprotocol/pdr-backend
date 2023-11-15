from unittest.mock import patch, MagicMock

from enforce_typing import enforce_types
import pytest

from pdr_backend.trueval.trueval_agent_base import get_trueval
from pdr_backend.trueval.trueval_agent_single import TruevalAgentSingle
from pdr_backend.trueval.trueval_config import TruevalConfig
from pdr_backend.util.web3_config import Web3Config


@enforce_types
def test_new_agent(trueval_config):
    agent_ = TruevalAgentSingle(trueval_config, get_trueval)
    assert agent_.config == trueval_config


@enforce_types
def test_process_slot(
    agent, slot, predictoor_contract_mock
):  # pylint: disable=unused-argument
    with patch.object(
        agent, "get_and_submit_trueval", return_value={"tx": "0x123"}
    ) as mock_submit:
        result = agent.process_slot(slot)
        assert result == {"tx": "0x123"}
        mock_submit.assert_called()


@enforce_types
def test_get_contract_info_caching(agent, predictoor_contract_mock):
    agent.get_contract_info("0x1")
    agent.get_contract_info("0x1")
    assert predictoor_contract_mock.call_count == 1
    predictoor_contract_mock.assert_called_once_with(agent.config.web3_config, "0x1")


@enforce_types
def test_submit_trueval_mocked_price_down(agent, slot, predictoor_contract_mock):
    with patch.object(agent, "get_trueval", return_value=(False, False)):
        result = agent.get_and_submit_trueval(
            slot, predictoor_contract_mock.return_value
        )
        assert result == {"tx": "0x123"}
        predictoor_contract_mock.return_value.submit_trueval.assert_called_once_with(
            False, 1692943200, False, True
        )


@enforce_types
def test_submit_trueval_mocked_price_up(agent, slot, predictoor_contract_mock):
    with patch.object(agent, "get_trueval", return_value=(True, False)):
        result = agent.get_and_submit_trueval(
            slot, predictoor_contract_mock.return_value
        )
        assert result == {"tx": "0x123"}
        predictoor_contract_mock.return_value.submit_trueval.assert_called_once_with(
            True, 1692943200, False, True
        )


@enforce_types
def test_submit_trueval_mocked_cancel(agent, slot, predictoor_contract_mock):
    with patch.object(agent, "get_trueval", return_value=(True, True)):
        result = agent.get_and_submit_trueval(
            slot, predictoor_contract_mock.return_value
        )
        assert result == {"tx": "0x123"}
        predictoor_contract_mock.return_value.submit_trueval.assert_called_once_with(
            True, 1692943200, True, True
        )


@enforce_types
def test_get_trueval_slot_up(
    agent, slot, predictoor_contract_mock
):  # pylint: disable=unused-argument
    with patch.object(agent, "get_trueval", return_value=(True, True)):
        result = agent.get_trueval_slot(slot)
        assert result == (True, True)


@enforce_types
def test_get_trueval_slot_down(
    agent, slot, predictoor_contract_mock
):  # pylint: disable=unused-argument
    with patch.object(agent, "get_trueval", return_value=(False, True)):
        result = agent.get_trueval_slot(slot)
        assert result == (False, True)


@enforce_types
def test_get_trueval_slot_cancel(
    agent, slot, predictoor_contract_mock
):  # pylint: disable=unused-argument
    with patch.object(agent, "get_trueval", return_value=(True, False)):
        result = agent.get_trueval_slot(slot)
        assert result == (True, False)


@enforce_types
def test_get_trueval_slot_too_many_requests_retry(
    agent, slot, predictoor_contract_mock
):  # pylint: disable=unused-argument
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


@enforce_types
def test_take_step(slot, agent):
    mocked_env = {
        "SLEEP_TIME": "1",
        "BATCH_SIZE": "1",
    }

    mocked_web3_config = MagicMock(spec=Web3Config)

    with patch.dict("os.environ", mocked_env), patch.object(
        agent.config, "web3_config", new=mocked_web3_config
    ), patch(
        "pdr_backend.trueval.trueval_agent_single.wait_until_subgraph_syncs"
    ), patch.object(
        TruevalConfig, "get_pending_slots", return_value=[slot]
    ), patch(
        "time.sleep"
    ), patch.object(
        TruevalConfig, "get_pending_slots", return_value=[slot]
    ), patch.object(
        TruevalAgentSingle, "process_slot"
    ) as ps_mock:
        agent.take_step()

    ps_mock.assert_called_once_with(slot)


@enforce_types
def test_run(slot, agent):
    mocked_env = {
        "SLEEP_TIME": "1",
        "BATCH_SIZE": "1",
    }

    mocked_web3_config = MagicMock(spec=Web3Config)

    with patch.dict("os.environ", mocked_env), patch.object(
        agent.config, "web3_config", new=mocked_web3_config
    ), patch(
        "pdr_backend.trueval.trueval_agent_single.wait_until_subgraph_syncs"
    ), patch(
        "time.sleep"
    ), patch.object(
        TruevalConfig, "get_pending_slots", return_value=[slot]
    ), patch.object(
        TruevalAgentSingle, "process_slot"
    ) as ps_mock:
        agent.run(True)

    ps_mock.assert_called_once_with(slot)


@enforce_types
def test_get_init_and_ts(agent):
    ts = 2000
    seconds_per_epoch = 300

    (initial_ts, end_ts) = agent.get_init_and_ts(ts, seconds_per_epoch)
    assert initial_ts == ts - 300
    assert end_ts == ts


# ----------------------------------------------
# Fixtures


@pytest.fixture(name="agent")
def agent_fixture(trueval_config):
    return TruevalAgentSingle(trueval_config, get_trueval)
