import logging
from collections import defaultdict
from typing import Dict, List, Tuple
from unittest.mock import Mock

from enforce_typing import enforce_types

from pdr_backend.contract.base_contract import BaseContract
from pdr_backend.contract.fixed_rate import FixedRate
from pdr_backend.contract.token import Token
from pdr_backend.util.constants import MAX_UINT, ZERO_ADDRESS
from pdr_backend.util.mathutil import string_to_bytes32
from pdr_backend.util.time_types import UnixTimeS
from pdr_backend.util.currency_types import Wei, Eth

logger = logging.getLogger("feed_contract")


@enforce_types
class FeedContract(BaseContract):  # pylint: disable=too-many-public-methods
    def __init__(self, web3_pp, address: str):
        super().__init__(web3_pp, address, "ERC20Template3")
        self.set_token(web3_pp)

        # return Wei(0) for unknown keys
        self.last_allowance: Dict[str, Wei] = defaultdict(lambda: Wei(0))

    def set_token(self, web3_pp):
        stake_token = self.get_stake_token()
        self.token = Token(web3_pp, stake_token)

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
        logger.info("Price of feed: %s OCEAN", baseTokenAmt_wei.to_eth())

        # approve
        logger.info("Approve spend OCEAN: begin")
        self.token.approve(self.contract_instance.address, baseTokenAmt_wei)
        logger.info("Approve spend OCEAN: done")

        # buy 1 DT
        call_params = self.web3_pp.tx_call_params()
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
            baseTokenAmt_wei.amt_wei,  # maxBaseTokenAmount
            0,  # swapMarketFee
            ZERO_ADDRESS,  # marketFeeAddress
        )

        if gasLimit is None:
            try:
                logger.info("Estimate gasLimit: begin")
                gasLimit = self.contract_instance.functions.buyFromFreAndOrder(
                    orderParams, freParams
                ).estimate_gas(call_params)
            except Exception as e:
                logger.warning(
                    "Estimate gasLimit had error in estimate_gas(): %s. "
                    "Because of error, use get_max_gas() as workaround",
                    e,
                )
                gasLimit = self.config.get_max_gas()
        assert gasLimit is not None, "should have non-None gasLimit by now"
        logger.info("Estimate gasLimit: done. gasLimit={gasLimit}")
        call_params["gas"] = gasLimit + 1

        try:
            logger.info("buyFromFreAndOrder: begin")
            tx = self.contract_instance.functions.buyFromFreAndOrder(
                orderParams, freParams
            ).transact(call_params)
            if not wait_for_receipt:
                logger.info("buyFromFreAndOrder: WIP, didn't wait around")
                return tx
            tx = self.config.w3.eth.wait_for_transaction_receipt(tx)
            logger.info("buyFromFreAndOrder: waited around, it's done")
            return tx
        except Exception as e:
            logger.info("buyFromFreAndOrder hit an error: %s", e)
            return None

    def buy_many(self, n_to_buy: int, gasLimit=None, wait_for_receipt=False):
        """Buys multiple subscriptions and returns tx hashes"""
        if n_to_buy < 1:
            return None

        logger.info("Purchase %d subscriptions for this feed: begin", n_to_buy)
        txs = []

        for i in range(n_to_buy):
            logger.info("Purchase access #%s/%s for this feed", i + 1, n_to_buy)
            tx = self.buy_and_start_subscription(gasLimit, wait_for_receipt)
            txs.append(tx)
        logger.info("Purchase %d subscriptions for this feed: done", n_to_buy)
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

    def get_price(self) -> Wei:
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
        Whereas curEpoch returns the timestamp of current candle start...
        *This* function returns the 'epoch number' that increases
          by one each secondsPerEpoch seconds
        """
        current_epoch_ts = self.get_current_epoch_ts()
        seconds_per_epoch = self.get_secondsPerEpoch()
        return int(current_epoch_ts / seconds_per_epoch)

    def get_current_epoch_ts(self) -> UnixTimeS:
        """returns the current candle start timestamp"""
        return UnixTimeS(self.contract_instance.functions.curEpoch().call())

    def get_secondsPerEpoch(self) -> int:
        """How many seconds are in each epoch? (According to contract)"""
        return self.contract_instance.functions.secondsPerEpoch().call()

    def get_agg_predval(self, timestamp: UnixTimeS) -> Tuple[Eth, Eth]:
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
        call_params = self.web3_pp.tx_call_params()
        (nom_wei, denom_wei) = self.contract_instance.functions.getAggPredval(
            timestamp, auth
        ).call(call_params)

        nom_wei = Wei(nom_wei)
        denom_wei = Wei(denom_wei)

        return nom_wei.to_eth(), denom_wei.to_eth()

    def payout_multiple(self, slots: List[UnixTimeS], wait_for_receipt: bool = True):
        """Claims the payout for given slots"""
        call_params = self.web3_pp.tx_call_params()
        try:
            tx = self.contract_instance.functions.payoutMultiple(
                slots, self.config.owner
            ).transact(call_params)

            if not wait_for_receipt:
                return tx

            return self.config.w3.eth.wait_for_transaction_receipt(tx)
        except Exception as e:
            logger.error(e)
            return None

    def payout(self, slot, wait_for_receipt=False):
        """Claims the payout for one slot"""
        call_params = self.web3_pp.tx_call_params()
        try:
            tx = self.contract_instance.functions.payout(
                slot, self.config.owner
            ).transact(call_params)

            if not wait_for_receipt:
                return tx

            return self.config.w3.eth.wait_for_transaction_receipt(tx)
        except Exception as e:
            logger.error(e)
            return None

    def soonest_timestamp_to_predict(self, timestamp: UnixTimeS) -> int:
        """Returns the soonest epoch to predict (expressed as a timestamp)"""
        return UnixTimeS(
            self.contract_instance.functions.soonestEpochToPredict(timestamp).call()
        )

    def submit_prediction(
        self,
        predicted_value: bool,
        stake_amt: Eth,
        prediction_ts: UnixTimeS,
        wait_for_receipt=True,
    ):
        """
        @description
          Submits a prediction with the specified stake amount, to the contract.

        @arguments
          predicted_value: The predicted value (True or False)
          stake_amt: The amount of OCEAN to stake in prediction (in ETH, not wei)
          prediction_ts: The prediction timestamp == start a candle.
          wait_for_receipt:
            If True, waits for tx receipt after submission.
            If False, immediately after sending the transaction.
            Default is True.

        @return:
          If wait_for_receipt is True, returns the tx receipt.
          If False, returns the tx hash immediately after sending.
          If an exception occurs during the  process, returns None.
        """
        stake_amt_wei: Wei = stake_amt.to_wei()

        # Check allowance first, only approve if needed
        allowance: Wei = self.last_allowance[self.config.owner]
        if allowance == Wei(0):
            allowance_wei = self.token.allowance(
                self.config.owner, self.contract_address
            )
            self.last_allowance[self.config.owner] = allowance_wei
        if allowance < stake_amt_wei:
            try:
                self.token.approve(self.contract_address, Wei(MAX_UINT))
                self.last_allowance[self.config.owner] = Wei(MAX_UINT)
            except Exception as e:
                logger.error(
                    "Error while approving the contract to spend tokens: %s", e
                )
                return None

        call_params = self.web3_pp.tx_call_params()
        try:
            txhash = None
            if self.config.is_sapphire:
                res, txhash = self.send_encrypted_tx(
                    "submitPredval",
                    [predicted_value, stake_amt_wei.amt_wei, prediction_ts],
                )
                logger.info("Encrypted transaction status code: %s", res)
            else:
                tx = self.contract_instance.functions.submitPredval(
                    predicted_value, stake_amt_wei.amt_wei, prediction_ts
                ).transact(call_params)
                txhash = tx.hex()
            self.last_allowance[self.config.owner] -= stake_amt_wei  # type: ignore
            logger.info("Submitted prediction, txhash: %s", txhash)

            if not wait_for_receipt:
                return txhash

            return self.config.w3.eth.wait_for_transaction_receipt(txhash)
        except Exception as e:
            logger.error(e)
            return None

    def get_trueValSubmitTimeout(self):
        """Returns the timeout for submitting truevals, according to contract"""
        return self.contract_instance.functions.trueValSubmitTimeout().call()

    def get_prediction(self, slot: UnixTimeS, address: str):
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
        Returns the hash of the transaction.
        """
        call_params = self.web3_pp.tx_call_params()
        tx = self.contract_instance.functions.submitTrueVal(
            timestamp, trueval, cancel_round
        ).transact(call_params)
        logger.info("Submit trueval: txhash=%s", tx.hex())

        if wait_for_receipt:
            tx = self.config.w3.eth.wait_for_transaction_receipt(tx)

        return tx

    def redeem_unused_slot_revenue(self, timestamp, wait_for_receipt=True):
        """Redeem unused slot revenue."""
        call_params = self.web3_pp.tx_call_params()
        try:
            tx = self.contract_instance.functions.redeemUnusedSlotRevenue(
                timestamp
            ).transact(call_params)

            if not wait_for_receipt:
                return tx

            return self.config.w3.eth.wait_for_transaction_receipt(tx)
        except Exception as e:
            logger.error(e)
            return None

    def erc721_addr(self) -> str:
        """What's the ERC721 address from which this ERC20 feed was created?"""
        return self.contract_instance.functions.getERC721Address().call()


# =========================================================================
# utilities for testing


@enforce_types
def mock_feed_contract(
    contract_address: str,
    agg_predval: tuple = (1, 2),
) -> FeedContract:
    c = Mock(spec=FeedContract)
    c.contract_address = contract_address
    c.get_agg_predval.return_value = agg_predval
    return c
