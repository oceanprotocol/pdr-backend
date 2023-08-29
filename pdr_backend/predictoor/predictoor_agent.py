from abc import ABC
import time
from typing import Dict

from enforce_typing import enforce_types

from pdr_backend.predictoor.predictoor_config import PredictoorConfig

@enforce_types
class PredictoorAgent(ABC):
    """
    What it does
    - Fetches Predictoor contracts from subgraph, and filters them
    - Monitors each contract for epoch changes.
    - When a value can be predicted, call predict.py::predict_function()
    """
    
    def __init__(self, config: PredictoorConfig):
        self.config = config 
        self.feeds = self.config.get_feeds() # [addr] : feed
        self.contracts = self.config.get_contracts() # [addr] : contract

        self.prev_block_time: int = 0
        self.prev_block_number: int = 0
        self.prev_submitted_epochs = {addr : 0 for addr in self.feeds}
            
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
            did_submit = self._maybe_submit_prediction(addr, epoch)
            if did_submit:
                self.prev_submitted_epochs[addr] = epoch

    def _maybe_submit_prediction(self, addr: str, epoch: int, contract) -> bool:
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
        predval, stake = self.get_prediction(feed, target_time)

        # maybe exit early 
        if predval is None or stake <= 0:
            print(
                f"We do not submit, because prediction function returned "
                f"({predval}, {stake})"
            )
            return False

        # we have a prediction, let's submit it to the chain
        print(f"Contract:{addr}: submitting prediction for slot:{target_time}")
        contract.submit_prediction(predval, stake, target_time, True)

        return True

    def get_prediction(self, feed: dict, timestamp: str) \
            -> Tuple[bool, int]:
        """
        @description
          Given a feed, let's predict for a given timestamp.

        @arguments
          feed -- dict -- info about the trading pair. See appendix
          timestamp -- str -- when to make prediction for

        @return
          predval -- bool -- if True, it's predicting 'up'. If False, 'down'
          stake -- int -- amount to stake, in units of wei

        @notes
          Below is the default implementation, giving random predictions.
          You need to customize it to implement your own strategy.

        @appendix 
          The feed dict looks like:
          {
            "name" : "ETH-USDT", # name of trading pair
            "address" : "0x54b5ebeed85f4178c6cb98dd185067991d058d55", # DT3 contract

            "symbol" : "ETH-USDT", # symbol of the trading pair
            "pair" : "eth-usdt", # (??, see line above)
            "base" : "eth", # base currency of trading pair
            "quote" : "usdt", # quote currency of the trading pair (??, see line above)
            "source" : "kraken", # source exchange or platform
            "timeframe" : "5m", # timeframe for the trade signal. 5m = 5 minutes

            # you could pass in other info
            "previous_submitted_epoch" : 0,
            "blocks_per_epoch" : "60", 
            "blocks_per_subscription" : "86400",
          }

        ## About SECONDS_TILL_EPOCH_END

        If we want to predict the value for epoch E, we need to do it in epoch E - 2
        (latest.  Though we could predict for a distant future epoch if desired)

        And to do so, our tx needs to be confirmed in the last block of epoch
        (otherwise, it's going to be part of next epoch and our prediction tx
         will revert)

        But, for every prediction, there are several steps. Each takes time:
        - time to compute prediction (e.g. run model inference)
        - time to generate the tx
        - time until your pending tx in mempool is picked by miner
        - time until your tx is confirmed in a block

        To help, you can set envvar `SECONDS_TILL_EPOCH_END`. It controls how many
        seconds in advance of the epoch ending you want the prediction process to
        start. A predictoor can submit multiple predictions. However, only the final
        submission made before the deadline is considered valid.

        To clarify further: if this value is set to 60, the predictoor will be asked
        to predict in every block during the last 60 seconds before the epoch
        concludes.
        """
        pass
    
