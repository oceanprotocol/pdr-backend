from enforce_typing import enforce_types

from pdr_backend.models.erc721_factory import Erc721Factory
from pdr_backend.util.contract import get_address


@enforce_types
def test_Erc721Factory(web3_pp, web3_config):
    factory = Erc721Factory(web3_pp)
    assert factory is not None

    ocean_address = get_address(web3_pp, "Ocean")
    fre_address = get_address(web3_pp, "FixedPrice")

    rate = 3
    cut = 0.2

    nft_data = ("TestToken", "TT", 1, "", True, web3_config.owner)
    erc_data = (
        3,
        ["ERC20Test", "ET"],
        [
            web3_config.owner,
            web3_config.owner,
            web3_config.owner,
            ocean_address,
            ocean_address,
        ],
        [2**256 - 1, 0, 300, 3000, 30000],
        [],
    )
    fre_data = (
        fre_address,
        [
            ocean_address,
            web3_config.owner,
            web3_config.owner,
            web3_config.owner,
        ],
        [
            18,
            18,
            web3_config.w3.to_wei(rate, "ether"),
            web3_config.w3.to_wei(cut, "ether"),
            1,
        ],
    )

    logs_nft, logs_erc = factory.createNftWithErc20WithFixedRate(
        nft_data, erc_data, fre_data
    )

    assert len(logs_nft) > 0
    assert len(logs_erc) > 0
