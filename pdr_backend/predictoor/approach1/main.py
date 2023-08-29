import time
from typing import Dict

from enforce_typing import enforce_types

from pdr_backend.predictoor.base import PredictoorBaseConfig, get_feeds
from pdr_backend.predictoor.approach1.predict import get_prediction


@enforce_types
class PredictoorApproach1Config(PredictoorConfig):
    def __init__(self):
        super().__init__()
        self.get_prediction = get_prediction # set prediction function

@enforce_types
class PredictoorApproach1:
    """
    What it does
    - Fetches Predictoor contracts from subgraph, and filters them
    - Monitors each contract for epoch changes.
    - When a value can be predicted, call predict.py::predict_function()
    """
    
    def __init__(self):
        self.config = PredictoorApproach1Config()
        self.feeds = self.config.get_feeds() # [addr] : feed
        self.contracts = self.config.get_contracts() # [addr] : contract

        self.prev_block_time: int = 0
        self.prev_block_number: int = 0
        self.prev_submitted_epochs = {addr : 0 for addr in self._addrs()}
        
    def run(self):
        print("Starting main loop...")
        while True:
            self.take_step()
    
    def take_step(self):
        # base data
        w3 = self.config.web3_config.w3
        
        # at new block number yet?
        block_number = w3.eth.block_number
        if block_number <= self.prev_block_number:
            time.sleep(1)
            return
        self.prev_block_number = block_number

        # is new block ready yet?
        block = w3.eth.get_block(block_number, full_transactions=False)
        if not block:
            return
        self.prev_block_time = block["timestamp"]
        print(f"Got new block, with number {block_number} ")

        # do work at new block
        for addr in self._addrs():
            self._process_block_at_feed(addr, block["timestamp"])
    
    def _process_block_at_feed(self, addr: str, timestamp: str):
        #base data
        feed = self.feeds[addr]
        contract = self.contracts[addr]
        epoch = contract.get_current_epoch()
        s_per_epoch = contract.get_secondsPerEpoch()
        s_remaining_in_epoch = epoch * s_per_epoch + s_per_epoch - timestamp

        # print status
        print(
            f"{feed['name']} at address {addr}"
            f" is at epoch {epoch}"
            f". s_per_epoch: {s_per_epoch}, "
            f"s_remaining_in_epoch: {s_remaining_in_epoch}"
        )

        # maybe get payout for previous epoch
        if epoch > self.prev_submitted_epochs[addr] > 0:
            slot = epoch * s_per_epoch - s_per_epoch
            print(f"Contract:{addr} - Claiming revenue for slot:{slot}")
            contract.payout(slot, False)

        # maybe submit prediction
        if s_remaining_in_epoch <= self.config.s_until_epoch_end:
            did_submit = maybe_submit_prediction(addr, epoch)
            if did_submit:
                self.prev_submitted_epochs[addr] = epoch

    def maybe_submit_prediction(self, addr: str, epoch: int, contract) -> bool:
        """
        @description
          Compute prediction. If it's ready, submit it to chain.
        
        @arguments
          addr -- address of feed
          epoch -- epoch that we want the prediction for
          contract -- predictoor contract

        @return
          did_submit -- bool
        """
        # base data
        feed = self.feeds[addr]
        
        # compute the prediction via predict.py::get_prediction
        target_time = (epoch + 2) * contract.get_secondsPerEpoch()
        predval, stake = self.config.get_prediction(feed, target_time)

        # maybe exit early 
        if pred_aggval is None or pred_confidence <= 0:
            print(
                f"We do not submit, because prediction function returned "
                f"({pred_aggval}, {pred_confidence})"
            )
            return False

        # we have a prediction, let's submit it to the chain
        # (TO DO have a customizable function to handle this)
        stake_amount = self.stake_amount * pred_confidence / 100

        print(
            f"Contract:{addr} - "
            f"Submitting prediction for slot:{target_time}"
        )

        contract.submit_prediction(
            pred_aggval, stake_amount, target_time, True
        )

        return True
    
    def _addrs(self) -> List[str]:
        """Return addresses in a deterministic order."""
        assert self.feeds
        return sorted(self.feeds.keys())
            

@enforce_types
def main():
    p = PredictoorApproach1()
    p.run()

if __name__ == "__main__":
    main()
