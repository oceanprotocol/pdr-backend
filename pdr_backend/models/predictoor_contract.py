from typing import List, Tuple

from enforce_typing import enforce_types
from eth_keys import KeyAPI
from eth_keys.backends import NativeECCBackend

from pdr_backend.models.fixed_rate import FixedRate
from pdr_backend.models.token import Token
from pdr_backend.models.base_contract import BaseContract
from pdr_backend.util.constants import ZERO_ADDRESS, MAX_UINT
from pdr_backend.util.networkutil import is_sapphire_network, send_encrypted_tx
from pdr_backend.util.web3_config import Web3Config

_KEYS = KeyAPI(NativeECCBackend)


@enforce_types
class PredictoorContract(BaseContract):  # pylint: disable=too-many-public-methods
    def __init__(self, config: Web3Config, address: str):
        super().__init__(config, address, "ERC20Template3")
        stake_token = self.get_stake_token()
        self.token = Token(config, stake_token)
        self.last_allowance = 0

    def is_valid_subscription(self):
        return self.contract_instance.functions.isValidSubscription(
            self.config.owner
        ).call()

    def getid(self):
        return self.contract_instance.functions.getId().call()

    def get_empty_provider_fee(self):
        return {
            "providerFeeAddress": ZERO_ADDRESS,
            "providerFeeToken": ZERO_ADDRESS,
            "providerFeeAmount": 0,
            "v": 0,
            "r": 0,
            "s": 0,
            "validUntil": 0,
            "providerData": 0,
        }

    def string_to_bytes32(self, data):
        if len(data) > 32:
            myBytes32 = data[:32]
        else:
            myBytes32 = data.ljust(32, "0")
        return bytes(myBytes32, "utf-8")

    def get_auth_signature(self):
        valid_until = self.config.get_block("latest").timestamp + 3600
        message_hash = self.config.w3.solidity_keccak(
            ["address", "uint256"],
            [self.config.owner, valid_until],
        )
        pk = _KEYS.PrivateKey(self.config.account.key)
        prefix = "\x19Ethereum Signed Message:\n32"
        signable_hash = self.config.w3.solidity_keccak(
            ["bytes", "bytes"],
            [
                self.config.w3.to_bytes(text=prefix),
                self.config.w3.to_bytes(message_hash),
            ],
        )
        signed = _KEYS.ecdsa_sign(message_hash=signable_hash, private_key=pk)
        auth = {
            "userAddress": self.config.owner,
            "v": (signed.v + 27) if signed.v <= 1 else signed.v,
            "r": self.config.w3.to_hex(
                self.config.w3.to_bytes(signed.r).rjust(32, b"\0")
            ),
            "s": self.config.w3.to_hex(
                self.config.w3.to_bytes(signed.s).rjust(32, b"\0")
            ),
            "validUntil": valid_until,
        }
        return auth

    def get_max_gas(self):
        """Returns max block gas"""
        block = self.config.get_block(
            self.config.w3.eth.block_number, full_transactions=False
        )
        return int(block["gasLimit"] * 0.99)

    def buy_and_start_subscription(self, gasLimit=None, wait_for_receipt=True):
        """Buys 1 datatoken and starts a subscription"""
        fixed_rates = self.get_exchanges()
        if not fixed_rates:
            return None

        (fixed_rate_address, exchange_id) = fixed_rates[0]

        # get datatoken price
        exchange = FixedRate(self.config, fixed_rate_address)
        (baseTokenAmount, _, _, _) = exchange.get_dt_price(exchange_id)

        # approve
        self.token.approve(self.contract_instance.address, baseTokenAmount)

        # buy 1 DT
        gasPrice = self.config.w3.eth.gas_price
        provider_fees = self.get_empty_provider_fee()
        try:
            orderParams = (
                self.config.owner,
                0,
                (
                    ZERO_ADDRESS,
                    ZERO_ADDRESS,
                    0,
                    0,
                    self.string_to_bytes32(""),
                    self.string_to_bytes32(""),
                    provider_fees["validUntil"],
                    self.config.w3.to_bytes(b""),
                ),
                (ZERO_ADDRESS, ZERO_ADDRESS, 0),
            )
            freParams = (
                self.config.w3.to_checksum_address(fixed_rate_address),
                self.config.w3.to_bytes(exchange_id),
                baseTokenAmount,
                0,
                ZERO_ADDRESS,
            )
            call_params = {
                "from": self.config.owner,
                "gasPrice": gasPrice,
                # 'nonce': self.config.w3.eth.get_transaction_count(self.config.owner),
            }
            if gasLimit is None:
                try:
                    gasLimit = self.contract_instance.functions.buyFromFreAndOrder(
                        orderParams, freParams
                    ).estimate_gas(call_params)
                except Exception as e:
                    print("Estimate gas failed")
                    print(e)
                    gasLimit = self.get_max_gas()
            call_params["gas"] = gasLimit + 1
            tx = self.contract_instance.functions.buyFromFreAndOrder(
                orderParams, freParams
            ).transact(call_params)
            if not wait_for_receipt:
                return tx
            return self.config.w3.eth.wait_for_transaction_receipt(tx)
        except Exception as e:
            print(e)
            return None

    def buy_many(self, how_many, gasLimit=None, wait_for_receipt=False):
        """Buys multiple accesses and returns tx hashes"""
        txs = []
        if how_many < 1:
            return None
        print(f"Buying {how_many} accesses....")
        for _ in range(0, how_many):
            txs.append(self.buy_and_start_subscription(gasLimit, wait_for_receipt))
        return txs

    def get_exchanges(self):
        return self.contract_instance.functions.getFixedRates().call()

    def get_stake_token(self):
        return self.contract_instance.functions.stakeToken().call()

    def get_price(self) -> int:
        fixed_rates = self.get_exchanges()
        if not fixed_rates:
            return 0
        (fixed_rate_address, exchange_id) = fixed_rates[0]
        # get datatoken price
        exchange = FixedRate(self.config, fixed_rate_address)
        (baseTokenAmount, _, _, _) = exchange.get_dt_price(exchange_id)
        return baseTokenAmount

    def get_current_epoch(self) -> int:
        # curEpoch returns the timestamp of current candle start
        # this function returns the "epoch number" that increases
        #   by one each secondsPerEpoch seconds
        current_epoch_ts = self.get_current_epoch_ts()
        seconds_per_epoch = self.get_secondsPerEpoch()
        return int(current_epoch_ts / seconds_per_epoch)

    def get_current_epoch_ts(self) -> int:
        """returns the current candle start timestamp"""
        return self.contract_instance.functions.curEpoch().call()

    def get_secondsPerEpoch(self) -> int:
        return self.contract_instance.functions.secondsPerEpoch().call()

    def get_agg_predval(self, timestamp) -> Tuple[float, float]:
        auth = self.get_auth_signature()
        (nom_wei, denom_wei) = self.contract_instance.functions.getAggPredval(
            timestamp, auth
        ).call({"from": self.config.owner})
        nom = float(self.config.w3.from_wei(nom_wei, "ether"))
        denom = float(self.config.w3.from_wei(denom_wei, "ether"))
        return nom, denom

    def payout_multiple(self, slots: List[int], wait_for_receipt=True):
        """Claims the payout for given slots"""
        gasPrice = self.config.w3.eth.gas_price
        try:
            tx = self.contract_instance.functions.payoutMultiple(
                slots, self.config.owner
            ).transact({"from": self.config.owner, "gasPrice": gasPrice})
            if not wait_for_receipt:
                return tx
            return self.config.w3.eth.wait_for_transaction_receipt(tx)
        except Exception as e:
            print(e)
            return None

    def payout(self, slot, wait_for_receipt=False):
        """Claims the payout for a slot"""
        gasPrice = self.config.w3.eth.gas_price
        try:
            tx = self.contract_instance.functions.payout(
                slot, self.config.owner
            ).transact({"from": self.config.owner, "gasPrice": gasPrice})
            if not wait_for_receipt:
                return tx
            return self.config.w3.eth.wait_for_transaction_receipt(tx)
        except Exception as e:
            print(e)
            return None

    def soonest_timestamp_to_predict(self, timestamp):
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

        gasPrice = self.config.w3.eth.gas_price
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
                ).transact({"from": self.config.owner, "gasPrice": gasPrice})
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
        return self.contract_instance.functions.trueValSubmitTimeout().call()

    def get_prediction(self, slot: int, address: str):
        auth_signature = self.get_auth_signature()
        return self.contract_instance.functions.getPrediction(
            slot, address, auth_signature
        ).call({"from": self.config.owner})

    def submit_trueval(self, trueval, timestamp, cancel_round, wait_for_receipt=True):
        gasPrice = self.config.w3.eth.gas_price
        tx = self.contract_instance.functions.submitTrueVal(
            timestamp, trueval, cancel_round
        ).transact({"from": self.config.owner, "gasPrice": gasPrice})
        print(f"Submitted trueval, txhash: {tx.hex()}")
        if not wait_for_receipt:
            return tx
        return self.config.w3.eth.wait_for_transaction_receipt(tx)

    def redeem_unused_slot_revenue(self, timestamp, wait_for_receipt=True):
        gasPrice = self.config.w3.eth.gas_price
        try:
            tx = self.contract_instance.functions.redeemUnusedSlotRevenue(
                timestamp
            ).transact({"from": self.config.owner, "gasPrice": gasPrice})
            if not wait_for_receipt:
                return tx
            return self.config.w3.eth.wait_for_transaction_receipt(tx)
        except Exception as e:
            print(e)
            return None

    def get_block(self, block):
        return self.config.get_block(block)

    def erc721_addr(self) -> str:
        return self.contract_instance.functions.getERC721Address().call()
