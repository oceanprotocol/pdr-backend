from typing import List
from enforce_typing import enforce_types
from pdr_backend.contract.base_contract import BaseContract
from pdr_backend.util.currency_types import Wei
from pdr_backend.util.time_types import UnixTimeS


@enforce_types
class PredSubmitterManager(BaseContract):
    def __init__(self, web3_pp, address: str):
        """
        @description
          Initialize the PredSubmitterManager object with a web3 provider and contract address.

        @arguments
          web3_pp -- Web3 provider for interacting with the blockchain.
          address -- str, the address of the PredSubmitterManager contract.
        """
        super().__init__(web3_pp, address, "PredSubmitterManager")

    def predictoor_up_address(self) -> str:
        """
        @description
          Returns the address of the upward predictoor contract.

        @return
          address -- str, address of the upward predictoor contract.
        """
        return self.contract_instance.functions.instanceUp().call()

    def predictoor_down_address(self) -> str:
        """
        @description
          Returns the address of the downward predictoor contract.

        @return
          address -- str, address of the downward predictoor contract.
        """
        return self.contract_instance.functions.instanceDown().call()

    def claim_dfrewards(
        self, token_addr: str, dfrewards_addr: str, wait_for_receipt=True
    ):
        """
        @description
          Claims DF rewards for the given token from the DFRewards contract.

        @arguments
          token_addr -- str, address of the token contract.
          dfrewards_addr -- str, address of the DFRewards contract.
          wait_for_receipt -- bool, if True, waits for the transaction receipt.

        @return
          tx -- transaction hash if wait_for_receipt is False, else the transaction receipt.
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
        feeds: list,
        epoch: UnixTimeS,
        wait_for_receipt=True,
    ):
        """
        @description
          Submits predictions for both upward and downward instances.

        @arguments
          stakes_up -- list of Wei, stakes for the upward predictions.
          stakes_down -- list of Wei, stakes for the downward predictions.
          feeds -- list of str, addresses of the feeds for predictions.
          epoch -- int, epoch start time for the predictions.
          wait_for_receipt -- bool, if True, waits for the transaction receipt.

        @return
          tx -- transaction hash if wait_for_receipt is False, else the transaction receipt.
        """
        stakes_up_wei = [s.amt_wei for s in stakes_up]
        stakes_down_wei = [s.amt_wei for s in stakes_down]
        if self.config.is_sapphire:
            res, tx = self.send_encrypted_tx(
                "submit", [stakes_up_wei, stakes_down_wei, feeds, epoch]
            )
            print("Encrypted transaction status code: %s", res)
        else:
            call_params = self.web3_pp.tx_call_params()
            tx = self.contract_instance.functions.submit(
                stakes_up_wei, stakes_down_wei, feeds, epoch
            ).transact(call_params)
        if not wait_for_receipt:
            return tx

        return self.config.w3.eth.wait_for_transaction_receipt(tx)

    def get_payout(self, epochs: list, feeds: list, wait_for_receipt=True):
        """
        @description
          Claims payouts for given list of epochs for both upward and downward predictions.

        @arguments
          epochs -- list of int, epoch timestamps for the predictions to claim payouts for.
          feeds -- list of str, addresses of the feeds for which to claim payouts.
          wait_for_receipt -- bool, if True, waits for the transaction receipt.

        @return
          tx -- transaction hash if wait_for_receipt is False, else the transaction receipt.
        """
        call_params = self.web3_pp.tx_call_params()
        tx = self.contract_instance.functions.getPayout(epochs, feeds).transact(
            call_params
        )

        if not wait_for_receipt:
            return tx

        return self.config.w3.eth.wait_for_transaction_receipt(tx)

    def transfer_erc20(self, token: str, to: str, amount: Wei, wait_for_receipt=True):
        """
        @description
          Transfers any ERC20 token from this contract to another address.

        @arguments
          token -- str, address of the ERC20 token contract.
          to -- str, address of the recipient.
          amount -- int, amount of tokens to transfer.
          wait_for_receipt -- bool, if True, waits for the transaction receipt.

        @return
          tx -- transaction hash if wait_for_receipt is False, else the transaction receipt.
        """
        call_params = self.web3_pp.tx_call_params()
        tx = self.contract_instance.functions.transferERC20(
            token, to, amount.amt_wei
        ).transact(call_params)

        if not wait_for_receipt:
            return tx

        return self.config.w3.eth.wait_for_transaction_receipt(tx)

    def version(self) -> str:
        """
        @description
          Returns the version of the PredSubmitterManager contract.

        @return
          version -- str, version of the contract.
        """
        return self.contract_instance.functions.version().call()

    def approve_ocean(self, feeds: list, wait_for_receipt=True):
        """
        @description
          Approves infinite OCEAN tokens from the instances to the feeds.

        @arguments
          feeds -- list of str, addresses of the feeds to approve tokens for.
          wait_for_receipt -- bool, if True, waits for the transaction receipt.

        @return
          tx -- transaction hash if wait_for_receipt is False, else the transaction receipt.
        """
        call_params = self.web3_pp.tx_call_params()
        tx = self.contract_instance.functions.approveOcean(feeds).transact(call_params)

        if not wait_for_receipt:
            return tx

        return self.config.w3.eth.wait_for_transaction_receipt(tx)

    def transfer(self, wait_for_receipt=True):
        """
        @description
          Transfers native tokens from this contract to the owner.

        @arguments
          wait_for_receipt -- bool, if True, waits for the transaction receipt.

        @return
          tx -- transaction hash if wait_for_receipt is False, else the transaction receipt.
        """
        call_params = self.web3_pp.tx_call_params()
        tx = self.contract_instance.functions.transfer().transact(call_params)

        if not wait_for_receipt:
            return tx

        return self.config.w3.eth.wait_for_transaction_receipt(tx)
