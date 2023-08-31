import time
from typing import Dict, Tuple

from enforce_typing import enforce_types

from pdr_backend.models.feed import Feed
from pdr_backend.predictoor.approach1.predictoor_config1 import \
    PredictoorConfig1


@enforce_types
class PredictoorAgent1:
    """
    What it does
    - Fetches Predictoor contracts from subgraph, and filters them
    - Monitors each contract for epoch changes.
    - When a value can be predicted, call predict.py::predict_function()
    """
    
    def __init__(self, config: PredictoorConfig1):
        self.config = config
        
        self.feeds: Dict[str,Feed] = self.config.get_feeds() # [addr] : Feed
        
        feed_addrs = list(self.feeds.keys())
        self.contracts = self.config.get_contracts(feed_addrs) # [addr] : contract

        self.prev_block_time: int = 0
        self.prev_block_number: int = 0
        self.prev_submitted_epochs = {addr : 0 for addr in self.feeds}


        print("\n" + "="*100)
        print("Feeds:")
        for addr, feed in self.feeds.items():
            print(f"  {feed}, full addr is {addr}")
        print()
            
    def run(self):
        print("Starting main loop...")
        while True:
            self.take_step()
    
    def take_step(self):
        # at new block number yet?
        w3 = self.config.web3_config.w3
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
        for addr in self.feeds:
            self._process_block_at_feed(addr, block["timestamp"])
    
    def _process_block_at_feed(self, addr: str, timestamp: int) -> tuple:
        """Returns (predval, stake, submitted)"""
        #base data
        feed, contract = self.feeds[addr], self.contracts[addr]
        epoch = contract.get_current_epoch()
        s_per_epoch = feed.seconds_per_epoch
        s_remaining_in_epoch = epoch * s_per_epoch + s_per_epoch - timestamp

        # print status
        print("\n" + "="*100) 
        print("Begin processing block for {feed}, timestamp={timestamp}")
        print(f"  epoch={epoch}")
        print(f"  s_per_epoch={s_per_epoch}")
        print(f"  s_remaining_in_epoch={s_remaining_in_epoch}")
        print(f"  prev submitted epoch={self.prev_submitted_epochs[addr]}")

        # maybe get payout for previous epoch
        if epoch > self.prev_submitted_epochs[addr] > 0:
            slot = epoch * s_per_epoch - s_per_epoch
            print(f"  Claim $ for previous epoch at timestamp=slot:{slot}")
            contract.payout(slot, False)

        # within the time window to submit prediction?
        if s_remaining_in_epoch > self.config.s_until_epoch_end:
            print("  Quit processing block: not in time window to submit")
            return (None, None, False)

        # compute prediction; exit if no good
        target_time = (epoch + 2) * contract.get_secondsPerEpoch()
        print(f"  We'll make a prediction for target_time=slot={target_time}")
        
        predval, stake = self.get_prediction(addr, target_time)
        print(f"  Predicted: predval={predval}, stake={stake}")
        if predval is None or stake <= 0:
            print("  Quit processing block: We can't use this predval/stake.")
            return (None, None, False)

        # submit prediction to chain
        print("  We can use this prediction. Let's submit to chain..")
        contract.submit_prediction(predval, stake, target_time, True)
        self.prev_submitted_epochs[addr] = epoch
        print("  Done processing block. Successfully submitted predval/stake.")
        return (predval, stake, True)

    def get_prediction(self, addr: str, timestamp: str) -> Tuple[bool, int]:
        """
        @description
          Given a feed, let's predict for a given timestamp.

        @arguments
          addr -- str -- address of the trading pair
          timestamp -- str -- when to make prediction for

        @return
          predval -- bool -- if True, it's predicting 'up'. If False, 'down'
          stake -- int -- amount to stake, in units of wei

        @notes
          Below is the default implementation, giving random predictions.
          You need to customize it to implement your own strategy.
        """
        feed = self.feeds[addr]

        # Pick random prediction & random stake. You need to customize this.
        import random
        predval = bool(random.getrandbits(1))
        stake = random.randint(10, 1000)

        return (predval, stake)

