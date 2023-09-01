from copy import deepcopy
from unittest.mock import patch
import pytest

from pdr_backend.trueval.trueval_agent_base import get_trueval
from pdr_backend.trueval.trueval_agent_batch import TruevalAgentBatch, TruevalSlot
from pdr_backend.util.constants import ZERO_ADDRESS


def test_new_agent(trueval_config):
    agent = TruevalAgentBatch(trueval_config, get_trueval, ZERO_ADDRESS)
    assert agent.config == trueval_config
    assert agent.predictoor_batcher.contract_address == ZERO_ADDRESS


def test_process_trueval_slot_up(agent, slot, predictoor_contract_mock):
    with patch.object(agent, "get_trueval", return_value=(True, False)):
        slot = TruevalSlot(slot_number=slot.slot_number, feed=slot.feed)
        agent.process_trueval_slot(slot)

        assert slot.cancel == False
        assert slot.trueval == True


def test_process_trueval_slot_down(agent, slot, predictoor_contract_mock):
    with patch.object(agent, "get_trueval", return_value=(False, False)):
        slot = TruevalSlot(slot_number=slot.slot_number, feed=slot.feed)
        agent.process_trueval_slot(slot)

        assert slot.cancel == False
        assert slot.trueval == False


def test_process_trueval_slot_cancel(agent, slot, predictoor_contract_mock):
    with patch.object(agent, "get_trueval", return_value=(False, True)):
        slot = TruevalSlot(slot_number=slot.slot_number, feed=slot.feed)
        agent.process_trueval_slot(slot)

        assert slot.cancel == True
        assert slot.trueval == False


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


def test_take_step(agent, slot):
    with patch.object(
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


@pytest.fixture()
def agent(trueval_config):
    return TruevalAgentBatch(trueval_config, get_trueval, ZERO_ADDRESS)
