from copy import deepcopy
from unittest.mock import MagicMock, Mock, patch

import pytest
from enforce_typing import enforce_types

from pdr_backend.trueval.trueval_agent import TruevalAgent, TruevalSlot
from pdr_backend.util.constants import ZERO_ADDRESS

PATH = "pdr_backend.trueval.trueval_agent"


@enforce_types
def test_trueval_agent_constructor(mock_ppss):
    agent_ = TruevalAgent(mock_ppss, ZERO_ADDRESS)
    assert agent_.ppss == mock_ppss
    assert agent_.predictoor_batcher.contract_address == ZERO_ADDRESS


@enforce_types
def test_get_contract_info_caching(agent, predictoor_contract_mock):
    agent.get_contract_info("0x1")
    agent.get_contract_info("0x1")
    assert predictoor_contract_mock.call_count == 1
    predictoor_contract_mock.assert_called_once_with(agent.ppss.web3_pp, "0x1")


@enforce_types
def test_get_trueval_slot(
    agent, slot, predictoor_contract_mock
):  # pylint: disable=unused-argument
    for trueval, cancel in [
        (True, True),  # up
        (False, True),  # down
        (True, False),  # cancel
    ]:
        with patch(f"{PATH}.get_trueval", Mock(return_value=(trueval, cancel))):
            result = agent.get_trueval_slot(slot)
            assert result == (trueval, cancel)


@enforce_types
def test_get_trueval_slot_too_many_requests_retry(
    agent, slot, predictoor_contract_mock
):  # pylint: disable=unused-argument
    mock_get_trueval = MagicMock(
        side_effect=[Exception("Too many requests"), (True, True)]
    )
    with patch(f"{PATH}.get_trueval", mock_get_trueval), patch(
        "time.sleep", return_value=None
    ) as mock_sleep:
        result = agent.get_trueval_slot(slot)
        mock_sleep.assert_called_once_with(60)
        assert result == (True, True)
        assert mock_get_trueval.call_count == 2


@enforce_types
def test_trueval_agent_run(agent):
    mock_take_step = Mock()
    with patch.object(agent, "take_step", mock_take_step):
        agent.run(testing=True)

    mock_take_step.assert_called_once()


@enforce_types
def test_trueval_agent_get_init_and_ts(agent):
    ts = 2000
    seconds_per_epoch = 300

    (initial_ts, end_ts) = agent.get_init_and_ts(ts, seconds_per_epoch)
    assert initial_ts == ts - 300
    assert end_ts == ts


@enforce_types
def test_process_trueval_slot(
    agent, slot, predictoor_contract_mock
):  # pylint: disable=unused-argument
    for trueval, cancel in [
        (True, True),  # up
        (False, True),  # down
        (True, False),  # cancel
    ]:
        with patch(f"{PATH}.get_trueval", Mock(return_value=(trueval, cancel))):
            slot = TruevalSlot(slot_number=slot.slot_number, feed=slot.feed)
            agent.process_trueval_slot(slot)

            assert slot.trueval == trueval
            assert slot.cancel == cancel


@enforce_types
def test_batch_submit_truevals(agent, slot):
    times = 3
    slot.feed.address = "0x0000000000000000000000000000000000c0ffee"
    trueval_slots = [
        TruevalSlot(feed=slot.feed, slot_number=i) for i in range(0, times)
    ]
    for i in trueval_slots:
        i.set_trueval(True)
        i.set_cancel(False)

    slot2 = deepcopy(slot)
    slot2.feed.address = "0x0000000000000000000000000000000000badbad"
    trueval_slots_2 = [
        TruevalSlot(feed=slot2.feed, slot_number=i) for i in range(0, times)
    ]
    for i in trueval_slots_2:
        i.set_trueval(True)
        i.set_cancel(False)

    trueval_slots.extend(trueval_slots_2)

    contract_addrs = [
        "0x0000000000000000000000000000000000C0FFEE",
        "0x0000000000000000000000000000000000baDbad",
    ]  # checksum
    epoch_starts = [list(range(0, times))] * 2
    truevals = [[True] * times, [True] * times]
    cancels = [[False] * times, [False] * times]

    with patch.object(
        agent.predictoor_batcher,
        "submit_truevals_contracts",
        return_value={"transactionHash": bytes.fromhex("badc0ffeee")},
    ) as mock:
        tx = agent.batch_submit_truevals(trueval_slots)
        assert tx == "badc0ffeee"
        mock.assert_called_with(contract_addrs, epoch_starts, truevals, cancels, True)


@enforce_types
def test_trueval_agent_take_step(agent, slot):
    with patch(f"{PATH}.wait_until_subgraph_syncs"), patch.object(
        agent, "get_batch", return_value=[slot]
    ) as mock_get_batch, patch.object(
        agent, "process_trueval_slot"
    ) as mock_process_trueval_slot, patch(
        "time.sleep"
    ), patch.object(
        agent, "batch_submit_truevals"
    ) as mock_batch_submit_truevals:
        agent.take_step()

        mock_get_batch.assert_called_once()
        call_args = mock_process_trueval_slot.call_args[0][0]
        assert call_args.slot_number == slot.slot_number
        assert call_args.feed == slot.feed

        call_args = mock_batch_submit_truevals.call_args[0][0]
        assert call_args[0].slot_number == slot.slot_number
        assert call_args[0].feed == slot.feed


# ----------------------------------------------
# Fixtures


@pytest.fixture(name="agent")
def agent_fixture(mock_ppss):
    return TruevalAgent(mock_ppss, ZERO_ADDRESS)
