from typing import List

from enforce_typing import enforce_types

from pdr_backend.contract.base_contract import BaseContract
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.util.currency_types import Wei
from pdr_backend.util.time_types import UnixTimeS


@enforce_types
class PredSubmitterMgr(BaseContract):
    def __init__(self, web3_pp: Web3PP, address: str):
        """
        @arguments
          web3_pp -- Web3 provider for interacting with the blockchain
          address -- address of PredSubmitterMgr contract
        """
        super().__init__(web3_pp, address, "PredSubmitterMgr")

    def predictoor_up_address(self) -> str:
        """
        @return
          address -- str, address of upward predictoor contract
        """
        return self.contract_instance.functions.instanceUp().call()

    def predictoor_down_address(self) -> str:
        """
        @return
         address -- address of downward predictoor contract
        """
        return self.contract_instance.functions.instanceDown().call()

    def claim_dfrewards(
        self, token_addr: str, dfrewards_addr: str, wait_for_receipt: bool = True
    ):
        """
        @description
          Claims DF rewards for the given token from the DFRewards contract

        @arguments
          token_addr -- address of token contract
          dfrewards_addr -- address of DFRewards contract
          wait_for_receipt -- if True, waits for the tx receipt

        @return
          tx -- tx hash if wait_for_receipt is False, else the tx receipt
        """
        call_params = self.web3_pp.tx_call_params()
        tx = self.contract_instance.functions.claimDFRewards(
            token_addr, dfrewards_addr
        ).transact(call_params)

        if not wait_for_receipt:
            return tx

        return self.config.w3.eth.wait_for_transaction_receipt(tx)

    def submit_prediction(
        self,
        stakes_up: List[Wei],
        stakes_down: List[Wei],
        feed_addrs: List[str],
        epoch: UnixTimeS,
        wait_for_receipt: bool = True,
    ):
        """
        @description
          Submits predictions for both upward and downward instances.

        @arguments
          stakes_up -- stakes for upward predictions
          stakes_down -- stakes for downward predictions
          feed_addrs -- addresses of tje feeds for predictions
          epoch -- epoch start time for the predictions
          wait_for_receipt -- if True, waits for the tx receipt

        @return
          tx -- tx hash if wait_for_receipt is False, else the tx receipt
        """
        stakes_up_wei = [s.amt_wei for s in stakes_up]
        stakes_down_wei = [s.amt_wei for s in stakes_down]
        if self.config.is_sapphire:
            _, tx = self.send_encrypted_tx(
                "submit", [stakes_up_wei, stakes_down_wei, feed_addrs, epoch]
            )
        else:
            call_params = self.web3_pp.tx_call_params()
            tx = self.contract_instance.functions.submit(
                stakes_up_wei, stakes_down_wei, feed_addrs, epoch
            ).transact(call_params)
        if not wait_for_receipt:
            return tx

        return self.config.w3.eth.wait_for_transaction_receipt(tx)

    def get_payout(
        self,
        epochs: List[UnixTimeS],
        feed_addrs: List[str],
        wait_for_receipt: bool = True,
    ):
        """
        @description
          Claims payouts for given list of epochs,
          for both upward and downward predictions.

        @arguments
          epochs -- epoch timestamps for the predictions to claim payouts for
          feed_addrs -- addresses of the feeds for which to claim payouts
          wait_for_receipt -- if True, waits for the tx receipt

        @return
          tx -- tx hash if wait_for_receipt is False, else the tx receipt.
        """
        call_params = self.web3_pp.tx_call_params()
        tx = self.contract_instance.functions.getPayout(epochs, feed_addrs).transact(
            call_params
        )

        if not wait_for_receipt:
            return tx

        return self.config.w3.eth.wait_for_transaction_receipt(tx)

    def transfer_erc20(
        self,
        token_addr: str,
        to_addr: str,
        amount: Wei,
        wait_for_receipt: bool = True,
    ):
        """
        @description
          Transfers any ERC20 token from this contract to another address

        @arguments
          token_addr -- address of the ERC20 token contract
          to_addr -- address of the recipient
          amount -- # tokens to transfer
          wait_for_receipt -- if True, waits for the tx receipt

        @return
          tx -- tx hash if wait_for_receipt is False, else the tx receipt
        """
        call_params = self.web3_pp.tx_call_params()
        tx = self.contract_instance.functions.transferERC20(
            token_addr, to_addr, amount.amt_wei
        ).transact(call_params)

        if not wait_for_receipt:
            return tx

        return self.config.w3.eth.wait_for_transaction_receipt(tx)

    def version(self) -> str:
        """
        @return
          version -- version of the PredSubmitterMgr contract
        """
        return self.contract_instance.functions.version().call()

    def approve_ocean(
        self,
        feed_addrs: List[str],
        wait_for_receipt: bool = True,
    ):
        """
        @description
          Approves infinite OCEAN tokens from the instances to the feeds

        @arguments
          feed_addrs -- addresses of the feeds to approve tokens for
          wait_for_receipt -- if True, waits for the tx receipt

        @return
          tx -- tx hash if wait_for_receipt is False, else the tx receipt
        """
        call_params = self.web3_pp.tx_call_params()
        tx = self.contract_instance.functions.approveOcean(feed_addrs).transact(
            call_params
        )

        if not wait_for_receipt:
            return tx

        return self.config.w3.eth.wait_for_transaction_receipt(tx)

    def transfer(self, wait_for_receipt: bool = True):
        """
        @description
          Transfers native tokens from this contract to the owner

        @arguments
          wait_for_receipt -- if True, waits for the tx receipt

        @return
          tx -- tx hash if wait_for_receipt is False, else the tx receipt
        """
        call_params = self.web3_pp.tx_call_params()
        tx = self.contract_instance.functions.transfer().transact(call_params)

        if not wait_for_receipt:
            return tx

        return self.config.w3.eth.wait_for_transaction_receipt(tx)
