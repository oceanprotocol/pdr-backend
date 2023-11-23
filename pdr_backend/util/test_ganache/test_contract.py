from pathlib import Path

from enforce_typing import enforce_types

from pdr_backend.util.contract import (
    get_address,
    get_addresses,
    get_contract_abi,
    get_contract_filename,
)


@enforce_types
def test_get_address(web3_pp):
    result = get_address(web3_pp, "Ocean")
    assert result is not None


@enforce_types
def test_get_addresses(web3_pp):
    result = get_addresses(web3_pp)
    assert result is not None


@enforce_types
def test_get_contract_abi(web3_pp):
    result = get_contract_abi("ERC20Template3", web3_pp.address_file)
    assert len(result) > 0 and isinstance(result, list)


@enforce_types
def test_get_contract_filename(web3_pp):
    result = get_contract_filename("ERC20Template3", web3_pp.address_file)
    assert result is not None and isinstance(result, Path)
