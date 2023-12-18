from enforce_typing import enforce_types
import pytest

from pdr_backend.util.contract import get_address
from pdr_backend.models.token import Token


@enforce_types
def test_base_contract(web3_pp, web3_config):
    OCEAN_address = get_address(web3_pp, "Ocean")

    # success
    Token(web3_pp, OCEAN_address)

    # catch failure
    web3_config = web3_pp.web3_config
    with pytest.raises(ValueError):
        Token(web3_config, OCEAN_address)
