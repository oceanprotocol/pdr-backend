from typing import Tuple

from enforce_typing import enforce_types

from pdr_backend.models.base_contract import BaseContract
from pdr_backend.util.mathutil import to_wei


@enforce_types
class FixedRate(BaseContract):
    def __init__(self, web3_pp, address: str):
        super().__init__(web3_pp, address, "FixedRateExchange")

    def get_dt_price(self, exchangeId) -> Tuple[int, int, int, int]:
        """
        @description
          # OCEAN needed to buy 1 datatoken

        @arguments
           exchangeId - a unique exchange identifier. Typically a string.

        @return
           baseTokenAmt_wei - # basetokens needed
           oceanFeeAmt_wei - fee to Ocean Protocol Community (OPC)
           publishMktFeeAmt_wei - fee to publish market
           consumeMktFeeAmt_wei - fee to consume market

        @notes
           Assumes consumeMktSwapFeeAmt = 0
        """
        return self.calcBaseInGivenOutDT(
            exchangeId,
            datatokenAmt_wei=to_wei(1),
            consumeMktSwapFeeAmt_wei=0,
        )

    def calcBaseInGivenOutDT(
        self,
        exchangeId,
        datatokenAmt_wei: int,
        consumeMktSwapFeeAmt_wei: int,
    ) -> Tuple[int, int, int, int]:
        """
        @description
           Given an exact target # datatokens, calculates # basetokens
           (OCEAN) needed to get it, and fee amounts too.

        @arguments
           exchangeId - a unique exchange identifier. Typically a string.
           datatokenAmt_wei - # datatokens to be exchanged
           consumeMktSwapFeeAmt - fee amount for consume market

        @return
           baseTokenAmt_wei - # OCEAN needed, in wei
           oceanFeeAmt_wei - fee to Ocean community (OPC)
           publishMktFeeAmt_wei - fee to publish market
           consumeMktFeeAmt_wei - fee to consume market
        """
        return self.contract_instance.functions.calcBaseInGivenOutDT(
            exchangeId,
            datatokenAmt_wei,
            consumeMktSwapFeeAmt_wei,
        ).call()
