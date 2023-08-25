from pathlib import Path

from enforce_typing import enforce_types

from pdr_backend.util.contract import (
    get_address,
    get_addresses,
    get_contract_abi,
    get_contract_filename,
)


@enforce_types
def test_get_address(chain_id):
    result = get_address(chain_id, "Ocean")
    assert result is not None


@enforce_types
def test_get_addresses(chain_id):
    result = get_addresses(chain_id)
    assert result is not None


@enforce_types
def test_get_contract_abi():
    result = get_contract_abi("ERC20Template3")
    assert len(result) > 0 and isinstance(result, list)


@enforce_types
def test_get_contract_filename():
    result = get_contract_filename("ERC20Template3")
    assert result is not None and isinstance(result, Path)
