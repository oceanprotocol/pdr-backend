import json
import os
import glob
import time
import hashlib
import artifacts

from pathlib import Path

import addresses
from eth_account import Account
from eth_account.signers.local import LocalAccount
from eth_keys import KeyAPI
from eth_keys.backends import NativeECCBackend
from sapphirepy import wrapper
from pathlib import Path
from web3 import Web3, HTTPProvider, WebsocketProvider
from web3.middleware import construct_sign_and_send_raw_middleware
from web3.logs import DISCARD

from pdr_backend.utils.constants import (
    ZERO_ADDRESS,
    SAPPHIRE_TESTNET_CHAINID,
    SAPPHIRE_MAINNET_CHAINID,
    MAX_UINT,
)

keys = KeyAPI(NativeECCBackend)


def is_sapphire_network(chain_id: int) -> bool:
    return chain_id in [SAPPHIRE_TESTNET_CHAINID, SAPPHIRE_MAINNET_CHAINID]


def send_encrypted_tx(
    contract_instance,
    function_name,
    args,
    pk,
    sender,
    receiver,
    rpc_url,
    value=0,  # in wei
    gasLimit=10000000,
    gasCost=0,  # in wei
    nonce=0,
) -> tuple:
    data = contract_instance.encodeABI(fn_name=function_name, args=args)
    return wrapper.send_encrypted_sapphire_tx(
        pk,
        sender,
        receiver,
        rpc_url,
        value,
        gasLimit,
        data,
        gasCost,
        nonce,
    )


class Web3Config:
    def __init__(self, rpc_url: str, private_key: str):
        self.rpc_url = rpc_url

        if rpc_url is None:
            raise ValueError("You must set RPC_URL variable")

        self.w3 = Web3(Web3.HTTPProvider(rpc_url))

        if private_key is not None:
            if not private_key.startswith("0x"):
                raise ValueError("Private key must start with 0x hex prefix")
            self.account: LocalAccount = Account.from_key(private_key)
            self.owner = self.account.address
            self.private_key = private_key
            self.w3.middleware_onion.add(
                construct_sign_and_send_raw_middleware(self.account)
            )


class Token:
    def __init__(self, config: Web3Config, address: str):
        self.contract_address = config.w3.to_checksum_address(address)
        self.contract_instance = config.w3.eth.contract(
            address=config.w3.to_checksum_address(address),
            abi=get_contract_abi("ERC20Template3"),
        )
        self.config = config

    def allowance(self, account, spender):
        return self.contract_instance.functions.allowance(account, spender).call()

    def balanceOf(self, account):
        return self.contract_instance.functions.balanceOf(account).call()

    def transfer(self, to: str, amount: int, sender, wait_for_receipt=True):
        gasPrice = self.config.w3.eth.gas_price
        tx = self.contract_instance.functions.transfer(to, int(amount)).transact(
            {"from": sender, "gasPrice": gasPrice}
        )
        if wait_for_receipt:
            return self.config.w3.eth.wait_for_transaction_receipt(tx)
        return tx

    def approve(self, spender, amount, wait_for_receipt=True):
        gasPrice = self.config.w3.eth.gas_price
        # print(f"Approving {amount} for {spender} on contract {self.contract_address}")
        try:
            tx = self.contract_instance.functions.approve(spender, amount).transact(
                {"from": self.config.owner, "gasPrice": gasPrice}
            )
            if not wait_for_receipt:
                return tx
            return self.config.w3.eth.wait_for_transaction_receipt(tx)
        except:
            return None


class PredictoorContract:
    def __init__(self, config: Web3Config, address: str):
        self.config = config
        self.contract_address = config.w3.to_checksum_address(address)
        self.contract_instance = config.w3.eth.contract(
            address=config.w3.to_checksum_address(address),
            abi=get_contract_abi("ERC20Template3"),
        )
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
        valid_until = int(time.time()) + 3600
        message_hash = self.config.w3.solidity_keccak(
            ["address", "uint256"],
            [self.config.owner, valid_until],
        )
        pk = keys.PrivateKey(self.config.account.key)
        prefix = "\x19Ethereum Signed Message:\n32"
        signable_hash = self.config.w3.solidity_keccak(
            ["bytes", "bytes"],
            [
                self.config.w3.to_bytes(text=prefix),
                self.config.w3.to_bytes(message_hash),
            ],
        )
        signed = keys.ecdsa_sign(message_hash=signable_hash, private_key=pk)
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
        block = self.config.w3.eth.get_block(
            self.config.w3.eth.block_number, full_transactions=False
        )
        return int(block["gasLimit"] * 0.99)

    def buy_and_start_subscription(self, gasLimit=None, wait_for_receipt=True):
        """Buys 1 datatoken and starts a subscription"""
        fixed_rates = self.get_exchanges()
        if not fixed_rates:
            return
        (fixed_rate_address, exchange_id) = fixed_rates[0]
        # get datatoken price
        exchange = FixedRate(self.config, fixed_rate_address)
        (
            baseTokenAmount,
            oceanFeeAmount,
            publishMarketFeeAmount,
            consumeMarketFeeAmount,
        ) = exchange.get_dt_price(exchange_id)
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
                #                    'nonce': self.config.w3.eth.get_transaction_count(self.config.owner),
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
            return
        print(f"Buying {how_many} accesses....")
        for i in range(0, how_many):
            txs.append(self.buy_and_start_subscription(gasLimit, wait_for_receipt))
        return txs

    def get_exchanges(self):
        return self.contract_instance.functions.getFixedRates().call()

    def get_stake_token(self):
        return self.contract_instance.functions.stakeToken().call()

    def get_price(self):
        fixed_rates = self.get_exchanges()
        if not fixed_rates:
            return
        (fixed_rate_address, exchange_id) = fixed_rates[0]
        # get datatoken price
        exchange = FixedRate(self.config, fixed_rate_address)
        (
            baseTokenAmount,
            oceanFeeAmount,
            publishMarketFeeAmount,
            consumeMarketFeeAmount,
        ) = exchange.get_dt_price(exchange_id)
        return baseTokenAmount

    def get_current_epoch(self) -> int:
        # curEpoch returns the timestamp of current candle start
        # this function returns the "epoch number" that increases by one each secondsPerEpoch seconds
        current_epoch_ts = self.get_current_epoch_ts()
        seconds_per_epoch = self.get_secondsPerEpoch()
        return int(current_epoch_ts / seconds_per_epoch)

    def get_current_epoch_ts(self) -> int:
        """returns the current candle start timestamp"""
        return self.contract_instance.functions.curEpoch().call()

    def get_secondsPerEpoch(self) -> int:
        return self.contract_instance.functions.secondsPerEpoch().call()

    def get_agg_predval(self, timestamp):
        """check subscription"""
        if not self.is_valid_subscription():
            print("Buying a new subscription...")
            self.buy_and_start_subscription(None, True)
            time.sleep(1)
        try:
            print("Reading contract values...")
            auth = self.get_auth_signature()
            (nom, denom) = self.contract_instance.functions.getAggPredval(
                timestamp, auth
            ).call({"from": self.config.owner})
            print(f" Got {nom} and {denom}")
            if denom == 0:
                return 0
            return nom / denom
        except Exception as e:
            print("Failed to call getAggPredval")
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
        stake_amount: int,
        prediction_ts: int,
        wait_for_receipt=True,
    ):
        """
        Submits a prediction with the specified stake amount to the smart contract on the blockchain.

        @param predicted_value: The predicted value (True or False)
        @param stake_amount: The amount of ETH to be staked on the prediction
        @param prediction_ts: The prediction timestamp, must be the start timestamp of a candle.
        @param wait_for_receipt: If True, the function waits for the transaction receipt after submission.
                                If False, it returns immediately after sending the transaction. Default is True.

        @return: If wait_for_receipt is True, returns the transaction receipt.
                If wait_for_receipt is False, returns the transaction hash immediately after sending the transaction.
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
                data = self.contract_instance.encodeABI(
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

    def get_prediction(self, slot):
        return self.contract_instance.functions.getPrediction(slot).call(
            {"from": self.config.owner}
        )

    def submit_trueval(
        self, true_val, timestamp, float_value, cancel_round, wait_for_receipt=True
    ):
        gasPrice = self.config.w3.eth.gas_price
        try:
            fl_value = self.config.w3.to_wei(str(float_value), "ether")
            tx = self.contract_instance.functions.submitTrueVal(
                timestamp, true_val, fl_value, cancel_round
            ).transact({"from": self.config.owner, "gasPrice": gasPrice})
            print(f"Submitted trueval, txhash: {tx.hex()}")
            if not wait_for_receipt:
                return tx
            return self.config.w3.eth.wait_for_transaction_receipt(tx)
        except Exception as e:
            print(e)
            return None

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
        return self.config.w3.eth.get_block(block)


class FixedRate:
    def __init__(self, config: Web3Config, address: str):
        self.contract_address = config.w3.to_checksum_address(address)
        self.contract_instance = config.w3.eth.contract(
            address=config.w3.to_checksum_address(address),
            abi=get_contract_abi("FixedRateExchange"),
        )
        self.config = config

    def get_dt_price(self, exchangeId):
        return self.contract_instance.functions.calcBaseInGivenOutDT(
            exchangeId, self.config.w3.to_wei("1", "ether"), 0
        ).call()


class ERC721Factory:
    def __init__(self, config: Web3Config, chain_id=None):
        if not chain_id:
            chain_id = config.w3.eth.chain_id
        address = get_address(chain_id, "ERC721Factory")
        if not address:
            raise ValueError("Cannot figure out ERC721Factory address")
        self.contract_address = config.w3.to_checksum_address(address)
        self.contract_instance = config.w3.eth.contract(
            address=config.w3.to_checksum_address(address),
            abi=get_contract_abi("ERC721Factory"),
        )
        self.config = config

    def createNftWithErc20WithFixedRate(self, NftCreateData, ErcCreateData, FixedData):
        #            gasPrice = self.config.w3.eth.gas_price
        call_params = {
            "from": self.config.owner,
            "gasPrice": 100000000000,
        }

        tx = self.contract_instance.functions.createNftWithErc20WithFixedRate(
            NftCreateData, ErcCreateData, FixedData
        ).transact(call_params)
        receipt = self.config.w3.eth.wait_for_transaction_receipt(tx)
        if receipt["status"] != 1:
            raise ValueError(f"createNftWithErc20WithFixedRate failed in {tx.hex()}")
        # print(receipt)
        logs = self.contract_instance.events.NFTCreated().process_receipt(
            receipt, errors=DISCARD
        )
        return logs[0]["args"]["newTokenAddress"]


class DataNft:
    def __init__(self, config: Web3Config, address: str):
        self.contract_address = config.w3.to_checksum_address(address)
        self.contract_instance = config.w3.eth.contract(
            address=config.w3.to_checksum_address(address),
            abi=get_contract_abi("ERC721Template"),
        )
        self.config = config

    def set_data(self, field_label, field_value, wait_for_receipt=True):
        """Set key/value data via ERC725, with strings for key/value"""
        field_label_hash = Web3.keccak(text=field_label)  # to keccak256 hash
        field_value_bytes = field_value.encode()  # to array of bytes
        #        gasPrice = self.config.w3.eth.gas_price
        call_params = {
            "from": self.config.owner,
            "gasPrice": 100000000000,
            "gas": 100000,
        }
        tx = self.contract_instance.functions.setNewData(
            field_label_hash, field_value_bytes
        ).transact(call_params)
        if wait_for_receipt:
            self.config.w3.eth.wait_for_transaction_receipt(tx)
        return tx

    def add_erc20_deployer(self, address, wait_for_receipt=True):
        #        gasPrice = self.config.w3.eth.gas_price
        call_params = {
            "from": self.config.owner,
            "gasPrice": 100000000000,
        }
        tx = self.contract_instance.functions.addToCreateERC20List(
            self.config.w3.to_checksum_address(address)
        ).transact(call_params)
        if wait_for_receipt:
            self.config.w3.eth.wait_for_transaction_receipt(tx)
        return tx

    def set_ddo(self, ddo, wait_for_receipt=True):
        #        gasPrice = self.config.w3.eth.gas_price
        call_params = {
            "from": self.config.owner,
            "gasPrice": 100000000000,
        }
        js = json.dumps(ddo)
        stored_ddo = Web3.to_bytes(text=js)
        tx = self.contract_instance.functions.setMetaData(
            1,
            "",
            str(self.config.owner),
            bytes([0]),
            stored_ddo,
            Web3.to_bytes(hexstr=hashlib.sha256(js.encode("utf-8")).hexdigest()),
            [],
        ).transact(call_params)
        if wait_for_receipt:
            self.config.w3.eth.wait_for_transaction_receipt(tx)
        return tx


def get_address(chain_id, contract_name):
    network = get_addresses(chain_id)
    if not network:
        raise ValueError(f"Cannot figure out {contract_name} address")
    address = network.get(contract_name)
    return address


def get_addresses(chain_id):
    address_filename = os.getenv("ADDRESS_FILE")
    path = None
    if address_filename:
        path = Path(address_filename)
    else:
        path = Path(str(os.path.dirname(addresses.__file__)) + "/address.json")

    if not path.exists():
        raise TypeError("Cannot find address.json")

    with open(path) as f:
        data = json.load(f)
    for name in data:
        network = data[name]
        if network["chainId"] == chain_id:
            return network
    return None


def get_contract_abi(contract_name):
    """Returns the abi for a contract name."""
    path = get_contract_filename(contract_name)

    if not path.exists():
        raise TypeError("Contract name does not exist in artifacts.")

    with open(path) as f:
        data = json.load(f)
        return data["abi"]


def get_contract_filename(contract_name):
    """Returns abi for a contract."""
    contract_basename = f"{contract_name}.json"

    # first, try to find locally
    address_filename = os.getenv("ADDRESS_FILE")
    path = None
    if address_filename:
        address_dir = os.path.dirname(address_filename)
        root_dir = os.path.join(address_dir, "..")
        os.chdir(root_dir)
        paths = glob.glob(f"**/{contract_basename}", recursive=True)
        if paths:
            assert len(paths) == 1, "had duplicates for {contract_basename}"
            path = paths[0]
            path = Path(path).expanduser().resolve()
            assert (
                path.exists()
            ), f"Found path = '{path}' via glob, yet path.exists() is False"
            return path
    # didn't find locally, so use use artifacts lib
    path = os.path.join(os.path.dirname(artifacts.__file__), "", contract_basename)
    path = Path(path).expanduser().resolve()
    if not path.exists():
        raise TypeError(f"Contract '{contract_name}' not found in artifacts.")
    return path
