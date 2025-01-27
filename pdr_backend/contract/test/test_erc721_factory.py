from unittest.mock import Mock, patch

import pytest
from enforce_typing import enforce_types

from pdr_backend.contract.erc721_factory import Erc721Factory
from pdr_backend.util.currency_types import Eth


@enforce_types
def test_Erc721Factory(web3_pp, web3_config):
    factory = Erc721Factory(web3_pp)
    assert factory is not None

    ocean_address = web3_pp.OCEAN_address
    fre_address = web3_pp.get_address("FixedPrice")

    rate = Eth(3).to_wei().amt_wei
    cut = Eth(0.2).to_wei().amt_wei

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
            rate,
            cut,
            1,
        ],
    )

    logs_nft, logs_erc = factory.createNftWithErc20WithFixedRate(
        nft_data, erc_data, fre_data
    )

    assert len(logs_nft) > 0
    assert len(logs_erc) > 0

    config = Mock()
    receipt = {"status": 0}
    config.w3.eth.wait_for_transaction_receipt.return_value = receipt


@enforce_types
def test_Erc721Factory_no_address(web3_pp):
    with patch.object(web3_pp, "get_address", return_value=None):
        with pytest.raises(ValueError):
            Erc721Factory(web3_pp)
