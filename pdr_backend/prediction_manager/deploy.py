import json
import os

from enforce_typing import enforce_types

from pdr_backend.ppss.web3_pp import Web3PP


@enforce_types
def deploy_prediction_manager_contract(web3_pp: Web3PP) -> str:
    web3_config = web3_pp.web3_config
    ocean_addr = web3_pp.get_address("Ocean")
    abi_path = os.path.join(
        os.path.dirname(__file__), "compiled_contracts", "PredSubmitterManager_abi.json"
    )

    bytecode_path = os.path.join(
        os.path.dirname(__file__),
        "compiled_contracts",
        "PredSubmitterManager_bytecode.bin",
    )

    with open(abi_path, "r") as abi_file:
        abi = json.load(abi_file)

    with open(bytecode_path, "r") as bytecode_file:
        bytecode = bytecode_file.read()

    PredSubmitterManager = web3_config.w3.eth.contract(abi=abi, bytecode=bytecode)
    tx_hash = PredSubmitterManager.constructor(ocean_addr).transact(
        web3_pp.tx_call_params()
    )
    tx_receipt = web3_config.w3.eth.wait_for_transaction_receipt(tx_hash)
    if tx_receipt["status"] != 1:
        raise ValueError("PredSubmitterManager contract deployment failed")
    if "contractAddress" not in tx_receipt:
        raise ValueError("PredSubmitterManager contract deployment failed")
    return str(tx_receipt["contractAddress"])
