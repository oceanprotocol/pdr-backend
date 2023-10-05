import time
from enforce_typing import enforce_types
from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.models.slot import Slot

from pdr_backend.trueval.trueval_agent_base import TruevalAgentBase
from pdr_backend.util.subgraph import wait_until_subgraph_syncs


@enforce_types
class TruevalAgentSingle(TruevalAgentBase):
    def take_step(self):
        wait_until_subgraph_syncs(self.config.web3_config, self.config.subgraph_url)
        pending_slots = self.get_batch()

        if len(pending_slots) == 0:
            print(f"No pending slots, sleeping for {self.config.sleep_time} seconds...")
            time.sleep(self.config.sleep_time)
            return

        for slot in pending_slots:
            print("-" * 30)
            print(f"Processing slot {slot.slot_number} for {slot.feed}")
            try:
                self.process_slot(slot)
            except Exception as e:
                print("An error occured", e)
        print(f"Done processing, sleeping for {self.config.sleep_time} seconds...")
        time.sleep(self.config.sleep_time)

    def process_slot(self, slot: Slot) -> dict:
        predictoor_contract, _ = self.get_contract_info(slot.feed.address)
        return self.get_and_submit_trueval(slot, predictoor_contract)

    def get_and_submit_trueval(
        self,
        slot: Slot,
        predictoor_contract: PredictoorContract,
    ) -> dict:
        try:
            (trueval, cancel) = self.get_trueval_slot(slot)

            # pylint: disable=line-too-long
            print(
                f"{slot.feed} - Submitting trueval {trueval} and slot:{slot.slot_number}"
            )
            tx = predictoor_contract.submit_trueval(
                trueval, slot.slot_number, cancel, True
            )
            return tx
        except Exception as e:
            print("Error while getting trueval:", e)
        return {}
