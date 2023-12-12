import time
from enforce_typing import enforce_types
from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.models.slot import Slot

from pdr_backend.trueval.base_trueval_agent import BaseTruevalAgent
from pdr_backend.util.subgraph import wait_until_subgraph_syncs


@enforce_types
class TruevalAgentSingle(BaseTruevalAgent):
    def take_step(self):
        wait_until_subgraph_syncs(
            self.ppss.web3_pp.web3_config, self.ppss.web3_pp.subgraph_url
        )
        pending_slots = self.get_batch()

        sleep_time = self.ppss.trueval_ss.sleep_time
        if len(pending_slots) == 0:
            print(f"No pending slots, sleeping for {sleep_time} seconds...")
            time.sleep(sleep_time)
            return

        for slot in pending_slots:
            print("-" * 30)
            print(f"Processing slot {slot.slot_number} for {slot.feed}")
            try:
                self.process_slot(slot)
            except Exception as e:
                print(f"An error occured: {e}")

        print(f"Done processing, sleeping for {sleep_time} seconds...")
        time.sleep(sleep_time)

    def process_slot(self, slot: Slot) -> dict:
        predictoor_contract, _ = self.get_contract_info(slot.feed.address)
        return self.get_and_submit_trueval(slot, predictoor_contract)

    def get_and_submit_trueval(
        self,
        slot: Slot,
        predictoor_contract: PredictoorContract,
    ) -> dict:
        # (don't wrap with try/except because the called func already does)
        (trueval, cancel_round) = self.get_trueval_slot(slot)

        print(
            f"Submit trueval: begin. For slot_number {slot.slot_number}"
            f" of {slot.feed}. Submitting trueval={trueval}"
        )
        try:
            wait_for_receipt = True
            tx = predictoor_contract.submit_trueval(
                trueval,
                slot.slot_number,
                cancel_round,
                wait_for_receipt,
            )
        except Exception as e:
            print(f"Error while submitting trueval: {e}")
            return {}

        print("Submit trueval: done")
        return tx
