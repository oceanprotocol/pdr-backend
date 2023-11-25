import json
import os

from enforce_typing import enforce_types
from eth_account import Account
from web3.logs import DISCARD

from pdr_backend.models.data_nft import DataNft
from pdr_backend.models.erc721_factory import ERC721Factory
from pdr_backend.util.constants import MAX_UINT
from pdr_backend.util.contract import get_address
from pdr_backend.util.web3_config import Web3Config


@enforce_types
def test_set_ddo():
    path = os.path.join(
        os.path.dirname(__file__), "../../tests/resources/ddo_v4_sample.json"
    )

    with open(path, "r") as file_handle:
        content = file_handle.read()
        ddo = json.loads(content)

    private_key = os.getenv("PRIVATE_KEY")
    owner = Account.from_key(  # pylint:disable=no-value-for-parameter
        private_key=private_key
    )
    rpc_url = os.getenv("RPC_URL")
    web3_config = Web3Config(rpc_url, private_key)
    factory = ERC721Factory(web3_config)
    ocean_address = get_address(web3_config.w3.eth.chain_id, "Ocean")
    fre_address = get_address(web3_config.w3.eth.chain_id, "FixedPrice")

    feeCollector = owner.address

    nft_data = ("NFT1", "NFT1", 1, "", True, owner.address)
    erc_data = (
        3,
        ["ERC20", "ERC20"],
        [
            owner.address,
            owner.address,
            feeCollector,
            ocean_address,
            ocean_address,
        ],
        [MAX_UINT, 0, 300, 300 * 24, 4 * 12 * 300],
        [],
    )

    rate = web3_config.w3.to_wei(3, "ether")
    cut = web3_config.w3.to_wei(0.2, "ether")
    fre_data = (
        fre_address,
        [ocean_address, owner.address, feeCollector, owner.address],
        [18, 18, rate, cut, 1],
    )
    logs_nft, _ = factory.createNftWithErc20WithFixedRate(nft_data, erc_data, fre_data)
    data_nft_address = logs_nft["newTokenAddress"]
    print(f"Deployed NFT: {data_nft_address}")
    data_nft = DataNft(web3_config, data_nft_address)

    tx = data_nft.set_ddo(ddo, wait_for_receipt=True)
    receipt = web3_config.w3.eth.wait_for_transaction_receipt(tx)
    event = data_nft.contract_instance.events.MetadataCreated().process_receipt(
        receipt, errors=DISCARD
    )[0]

    assert event
