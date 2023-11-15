from copy import deepcopy
from unittest.mock import patch

import pytest

from pdr_backend.trueval.trueval_agent_base import get_trueval
from pdr_backend.trueval.trueval_agent_batch import TruevalAgentBatch, TruevalSlot
from pdr_backend.util.constants import ZERO_ADDRESS


def test_new_agent(trueval_config):
    print(
        "RUNNING TEST_NEW_AGENT TEST -------------------------------------------------------------------------"
    )
    agent_ = TruevalAgentBatch(trueval_config, get_trueval, ZERO_ADDRESS)
    assert agent_.config == trueval_config
    assert agent_.predictoor_batcher.contract_address == ZERO_ADDRESS


def test_process_trueval_slot_up(
    agent_fixture, slot, predictoor_contract_mock
):  # pylint: disable=unused-argument
    print(
        "RUNNING TEST_PROCESS_TRUEVAL_SLOT_UP TEST -------------------------------------------------------------------------"
    )
    with patch.object(agent_fixture, "get_trueval", return_value=(True, False)):
        slot = TruevalSlot(slot_number=slot.slot_number, feed=slot.feed)
        agent_fixture.process_trueval_slot(slot)

        assert not slot.cancel
        assert slot.trueval


def test_process_trueval_slot_down(
    agent_fixture, slot, predictoor_contract_mock
):  # pylint: disable=unused-argument
    with patch.object(agent_fixture, "get_trueval", return_value=(False, False)):
        slot = TruevalSlot(slot_number=slot.slot_number, feed=slot.feed)
        agent_fixture.process_trueval_slot(slot)

        assert not slot.cancel
        assert not slot.trueval


def test_process_trueval_slot_cancel(
    agent_fixture, slot, predictoor_contract_mock
):  # pylint: disable=unused-argument
    with patch.object(agent_fixture, "get_trueval", return_value=(False, True)):
        slot = TruevalSlot(slot_number=slot.slot_number, feed=slot.feed)
        agent_fixture.process_trueval_slot(slot)

        assert slot.cancel
        assert not slot.trueval


def test_batch_submit_truevals(agent_fixture, slot):
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
        agent_fixture.predictoor_batcher,
        "submit_truevals_contracts",
        return_value={"transactionHash": bytes.fromhex("badc0ffeee")},
    ) as mock:
        tx = agent_fixture.batch_submit_truevals(trueval_slots)
        assert tx == "badc0ffeee"
        mock.assert_called_with(contract_addrs, epoch_starts, truevals, cancels, True)


def test_take_step(agent_fixture, slot):
    with patch.object(
        agent_fixture, "get_batch", return_value=[slot]
    ) as mock_get_batch, patch.object(
        agent_fixture, "process_trueval_slot"
    ) as mock_process_trueval_slot, patch(
        "time.sleep"
    ), patch.object(
        agent_fixture, "batch_submit_truevals"
    ) as mock_batch_submit_truevals:
        agent_fixture.take_step()

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
def agent_fixture(trueval_config):
    return TruevalAgentBatch(trueval_config, get_trueval, ZERO_ADDRESS)
