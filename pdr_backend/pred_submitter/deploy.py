#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
import os

from enforce_typing import enforce_types

from pdr_backend.ppss.web3_pp import Web3PP


@enforce_types
def deploy_pred_submitter_mgr_contract(web3_pp: Web3PP) -> str:
    web3_config = web3_pp.web3_config
    ocean_addr = web3_pp.get_address("Ocean")
    abi_path = os.path.join(
        os.path.dirname(__file__), "compiled_contracts", "PredSubmitterMgr_abi.json"
    )

    bytecode_path = os.path.join(
        os.path.dirname(__file__),
        "compiled_contracts",
        "PredSubmitterMgr_bytecode.bin",
    )

    with open(abi_path, "r") as abi_file:
        abi = json.load(abi_file)

    with open(bytecode_path, "r") as bytecode_file:
        bytecode = bytecode_file.read()

    call_params = web3_pp.tx_call_params()
    PredSubmitterMgr = web3_config.w3.eth.contract(abi=abi, bytecode=bytecode)
    unsigned = PredSubmitterMgr.constructor(ocean_addr).build_transaction(call_params)
    unsigned["nonce"] = web3_config.w3.eth.get_transaction_count(call_params["from"])
    signed = web3_config.w3.eth.account.sign_transaction(
        unsigned, private_key=web3_pp.private_key
    )
    tx_hash = web3_config.w3.eth.send_raw_transaction(signed.raw_transaction)
    tx_receipt = web3_config.w3.eth.wait_for_transaction_receipt(tx_hash)
    if tx_receipt["status"] != 1:
        raise ValueError("PredSubmitterMgr contract deployment failed")
    if "contractAddress" not in tx_receipt:
        raise ValueError("PredSubmitterMgr contract deployment failed")
    return str(tx_receipt["contractAddress"])
