from typing import List, Tuple
from unittest.mock import Mock

from enforce_typing import enforce_types

from pdr_backend.models.fixed_rate import FixedRate

from pdr_backend.models.token import Token
from pdr_backend.models.base_contract import BaseContract
from pdr_backend.util.constants import ZERO_ADDRESS, MAX_UINT
from pdr_backend.util.mathutil import string_to_bytes32, from_wei
from pdr_backend.util.networkutil import (
    is_sapphire_network,
    send_encrypted_tx,
    tx_call_params,
    get_max_gas,
)


@enforce_types
class PredictoorContract(BaseContract):  # pylint: disable=too-many-public-methods
    def __init__(self, web3_pp, address: str):
        super().__init__(web3_pp, address, "ERC20Template3")
        stake_token = self.get_stake_token()
        self.token = Token(web3_pp, stake_token)
        self.last_allowance = 0

    def is_valid_subscription(self):
        """Does this account have a subscription to this feed yet?"""
        return self.contract_instance.functions.isValidSubscription(
            self.config.owner
        ).call()

    def getid(self):
        """Return the ID of this contract."""
        return self.contract_instance.functions.getId().call()

    def buy_and_start_subscription(self, gasLimit=None, wait_for_receipt=True):
        """
        @description
          Buys 1 datatoken and starts a subscription.

        @return
          tx - transaction hash. Or, returns None if an error while transacting
        """
        exchanges = self.get_exchanges()
        if not exchanges:
            raise ValueError("No exchanges available")

        (exchange_addr, exchangeId) = exchanges[0]

        # get datatoken price
        exchange = FixedRate(self.web3_pp, exchange_addr)
        (baseTokenAmt_wei, _, _, _) = exchange.get_dt_price(exchangeId)
        print(f"  Price of feed: {from_wei(baseTokenAmt_wei)} OCEAN")

        # approve
        print("  Approve spend OCEAN: begin")
        self.token.approve(self.contract_instance.address, baseTokenAmt_wei)
        print("  Approve spend OCEAN: done")

        # buy 1 DT
        call_params = tx_call_params(self.web3_pp)
        orderParams = (  # OrderParams
            self.config.owner,  # consumer
            0,  # serviceIndex
            (  # providerFee, with zeroed values
                ZERO_ADDRESS,
                ZERO_ADDRESS,
                0,
                0,
                string_to_bytes32(""),
                string_to_bytes32(""),
                0,
                self.config.w3.to_bytes(b""),
            ),
            (  # consumeMarketFee, with zeroed values
                ZERO_ADDRESS,
                ZERO_ADDRESS,
                0,
            ),
        )
        freParams = (  # FreParams
            self.config.w3.to_checksum_address(exchange_addr),  # exchangeContract
            self.config.w3.to_bytes(exchangeId),  # exchangeId
            baseTokenAmt_wei,  # maxBaseTokenAmount
            0,  # swapMarketFee
            ZERO_ADDRESS,  # marketFeeAddress
        )

        if gasLimit is None:
            try:
                print("  Estimate gasLimit: begin")
                gasLimit = self.contract_instance.functions.buyFromFreAndOrder(
                    orderParams, freParams
                ).estimate_gas(call_params)
            except Exception as e:
                print(f"  Estimate gasLimit had error in estimate_gas(): {e}")
                print("  Because of error, use get_max_gas() as workaround")
                gasLimit = get_max_gas(self.config)
        assert gasLimit is not None, "should have non-None gasLimit by now"
        print(f"  Estimate gasLimit: done. gasLimit={gasLimit}")
        call_params["gas"] = gasLimit + 1

        try:
            print("  buyFromFreAndOrder: begin")
            tx = self.contract_instance.functions.buyFromFreAndOrder(
                orderParams, freParams
            ).transact(call_params)
            if not wait_for_receipt:
                print("  buyFromFreAndOrder: WIP, didn't wait around")
                return tx
            tx = self.config.w3.eth.wait_for_transaction_receipt(tx)
            print("  buyFromFreAndOrder: waited around, it's done")
            return tx
        except Exception as e:
            print("  buyFromFreAndOrder hit an error:")
            print(e)
            return None

    def buy_many(self, n_to_buy: int, gasLimit=None, wait_for_receipt=False):
        """Buys multiple subscriptions and returns tx hashes"""
        if n_to_buy < 1:
            return None
        print(f"Purchase {n_to_buy}  subscriptions for this feed: begin")
        txs = []
        for i in range(n_to_buy):
            print(f"Purchase access #{i+1}/{n_to_buy} for this feed")
            tx = self.buy_and_start_subscription(gasLimit, wait_for_receipt)
            txs.append(tx)
        print(f"Purchase {n_to_buy}  subscriptions for this feed: done")
        return txs

    def get_exchanges(self) -> List[Tuple[str, str]]:
        """
        @description
          Returns the fixed-rate exchanges created for this datatoken

        @return
          exchanges - list of (exchange_addr:str, exchangeId: str)
        """
        return self.contract_instance.functions.getFixedRates().call()

    def get_stake_token(self):
        """Returns the token used for staking & purchases. Eg OCEAN."""
        return self.contract_instance.functions.stakeToken().call()

    def get_price(self) -> int:
        """
        @description
          # OCEAN needed to buy 1 datatoken

        @return
           baseTokenAmt_wei - # OCEAN needed, in wei

        @notes
           Assumes consumeMktSwapFeeAmt = 0
        """
        exchanges = self.get_exchanges()  # fixed rate exchanges
        if not exchanges:
            raise ValueError("No exchanges available")
        (exchange_addr, exchangeId) = exchanges[0]

        exchange = FixedRate(self.web3_pp, exchange_addr)
        (baseTokenAmt_wei, _, _, _) = exchange.get_dt_price(exchangeId)
        return baseTokenAmt_wei

    def get_current_epoch(self) -> int:
        """
        curEpoch returns the timestamp of current candle start

        this function returns the 'epoch number' that increases
          by one each secondsPerEpoch seconds
        """
        current_epoch_ts = self.get_current_epoch_ts()
        seconds_per_epoch = self.get_secondsPerEpoch()
        return int(current_epoch_ts / seconds_per_epoch)

    def get_current_epoch_ts(self) -> int:
        """returns the current candle start timestamp"""
        return self.contract_instance.functions.curEpoch().call()

    def get_secondsPerEpoch(self) -> int:
        """How many seconds are in each epoch? (According to contract)"""
        return self.contract_instance.functions.secondsPerEpoch().call()

    def get_agg_predval(self, timestamp: int) -> Tuple[float, float]:
        """
        @description
          Get aggregated prediction value.

        @arguments
          timestamp -

        @return
          nom - numerator = # OCEAN staked for 'up' (in units of ETH, not wei)
          denom - denominator = total # OCEAN staked ("")
        """
        auth = self.config.get_auth_signature()
        call_params = tx_call_params(self.web3_pp)
        (nom_wei, denom_wei) = self.contract_instance.functions.getAggPredval(
            timestamp, auth
        ).call(call_params)
        return from_wei(nom_wei), from_wei(denom_wei)

    def payout_multiple(self, slots: List[int], wait_for_receipt=True):
        """Claims the payout for given slots"""
        call_params = tx_call_params(self.web3_pp)
        try:
            tx = self.contract_instance.functions.payoutMultiple(
                slots, self.config.owner
            ).transact(call_params)
            if not wait_for_receipt:
                return tx
            return self.config.w3.eth.wait_for_transaction_receipt(tx)
        except Exception as e:
            print(e)
            return None

    def payout(self, slot, wait_for_receipt=False):
        """Claims the payout for one slot"""
        call_params = tx_call_params(self.web3_pp)
        try:
            tx = self.contract_instance.functions.payout(
                slot, self.config.owner
            ).transact(call_params)
            if not wait_for_receipt:
                return tx
            return self.config.w3.eth.wait_for_transaction_receipt(tx)
        except Exception as e:
            print(e)
            return None

    def soonest_timestamp_to_predict(self, timestamp: int) -> int:
        """Returns the soonest epoch to predict (expressed as a timestamp)"""
        return self.contract_instance.functions.soonestEpochToPredict(timestamp).call()

    def submit_prediction(
        self,
        predicted_value: bool,
        stake_amount: float,
        prediction_ts: int,
        wait_for_receipt=True,
    ):
        """
        Submits a prediction with the specified stake amount, to the contract.

        @param predicted_value: The predicted value (True or False)
        @param stake_amount: The amount of ETH to be staked on the prediction
        @param prediction_ts: The prediction timestamp == start a candle.
        @param wait_for_receipt:
          If True, waits for tx receipt after submission.
          If False, immediately after sending the transaction.
          Default is True.

        @return:
          If wait_for_receipt is True, returns the tx receipt.
          If False, returns the tx hash immediately after sending.
          If an exception occurs during the  process, returns None.
        """
        amount_wei = self.config.w3.to_wei(str(stake_amount), "ether")

        # Check allowance first, only approve if needed
        if self.last_allowance <= 0:
            self.last_allowance = self.token.allowance(
                self.config.owner, self.contract_address
            )
        if self.last_allowance < amount_wei:
            try:
                self.token.approve(self.contract_address, MAX_UINT)
                self.last_allowance = MAX_UINT
            except Exception as e:
                print("Error while approving the contract to spend tokens:", e)
                return None

        call_params = tx_call_params(self.web3_pp)
        try:
            txhash = None
            if is_sapphire_network(self.config.w3.eth.chain_id):
                self.contract_instance.encodeABI(
                    fn_name="submitPredval",
                    args=[predicted_value, amount_wei, prediction_ts],
                )
                sender = self.config.owner
                receiver = self.contract_instance.address
                pk = self.config.account.key.hex()[2:]
                res, txhash = send_encrypted_tx(
                    self.contract_instance,
                    "submitPredval",
                    [predicted_value, amount_wei, prediction_ts],
                    pk,
                    sender,
                    receiver,
                    self.config.rpc_url,
                    0,
                    1000000,
                    0,
                    0,
                )
                print("Encrypted transaction status code:", res)
            else:
                tx = self.contract_instance.functions.submitPredval(
                    predicted_value, amount_wei, prediction_ts
                ).transact(call_params)
                txhash = tx.hex()
            self.last_allowance -= amount_wei
            print(f"Submitted prediction, txhash: {txhash}")
            if not wait_for_receipt:
                return txhash
            return self.config.w3.eth.wait_for_transaction_receipt(txhash)
        except Exception as e:
            print(e)
            return None

    def get_trueValSubmitTimeout(self):
        """Returns the timeout for submitting truevals, according to contract"""
        return self.contract_instance.functions.trueValSubmitTimeout().call()

    def get_prediction(self, slot: int, address: str):
        """Returns the prediction made by this account, for
        the specified time slot and address."""
        auth_signature = self.config.get_auth_signature()
        call_params = {"from": self.config.owner}
        return self.contract_instance.functions.getPrediction(
            slot, address, auth_signature
        ).call(call_params)

    def submit_trueval(self, trueval, timestamp, cancel_round, wait_for_receipt=True):
        """Submit true value for this feed, at the specified time.
        Alternatively, cancel this epoch (round).
        Can only be called by the owner.
        """
        call_params = tx_call_params(self.web3_pp)
        tx = self.contract_instance.functions.submitTrueVal(
            timestamp, trueval, cancel_round
        ).transact(call_params)
        print(f"Submitted trueval, txhash: {tx.hex()}")
        if not wait_for_receipt:
            return tx
        return self.config.w3.eth.wait_for_transaction_receipt(tx)

    def redeem_unused_slot_revenue(self, timestamp, wait_for_receipt=True):
        """Redeem unused slot revenue."""
        call_params = tx_call_params(self.web3_pp)
        try:
            tx = self.contract_instance.functions.redeemUnusedSlotRevenue(
                timestamp
            ).transact(call_params)
            if not wait_for_receipt:
                return tx
            return self.config.w3.eth.wait_for_transaction_receipt(tx)
        except Exception as e:
            print(e)
            return None

    def erc721_addr(self) -> str:
        """What's the ERC721 address from which this ERC20 feed was created?"""
        return self.contract_instance.functions.getERC721Address().call()


# =========================================================================
# utilities for testing


@enforce_types
def mock_predictoor_contract(
    contract_address: str,
    agg_predval: tuple = (1, 2),
) -> PredictoorContract:
    c = Mock(spec=PredictoorContract)
    c.contract_address = contract_address
    c.get_agg_predval.return_value = agg_predval
    return c
