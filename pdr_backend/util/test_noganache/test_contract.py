from pathlib import Path

from unittest.mock import patch
import pytest
from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.util.contract import (
    _condition_sapphire_keys,
    get_address,
    get_addresses,
    get_contract_abi,
    get_contract_filename,
)

_NETWORKS = [
    "sapphire-testnet",
    "sapphire-mainnet",
    "development",
]


@enforce_types
@pytest.mark.parametrize("network", _NETWORKS)
def test_contract_main(network):
    # setup

    ppss = mock_ppss(["binance BTC/USDT c 5m"], network)
    web3_pp = ppss.web3_pp
    assert web3_pp.network == network

    # tests
    assert get_address(web3_pp, "Ocean") is not None

    assert get_addresses(web3_pp) is not None

    result = get_contract_abi("ERC20Template3", web3_pp.address_file)
    assert len(result) > 0 and isinstance(result, list)

    result = get_contract_filename("ERC20Template3", web3_pp.address_file)
    assert result is not None and isinstance(result, Path)

    with pytest.raises(TypeError):
        get_contract_abi("xyz", web3_pp.address_file)


@enforce_types
@patch("pdr_backend.util.contract.get_addresses")
def test_get_addresses(mock_get_addresses):
    # setup
    network = "development"
    ppss = mock_ppss(["binance BTC/USDT c 5m"], network)
    web3_pp = ppss.web3_pp
    assert web3_pp.network == network

    mock_get_addresses.return_value = None

    # Work 1: validate network can't be found
    with pytest.raises(ValueError) as excinfo:
        get_address(web3_pp, "Ocean")

    assert 'Cannot find network "development"' in str(excinfo.value)

    mock_get_addresses.return_value = {
        "Ocean": "0x1234567890123456789012345678901234567890"
    }
    with pytest.raises(ValueError) as excinfo:
        get_address(web3_pp, "ERCUnknown")

    assert 'Cannot find contract "ERCUnknown"' in str(excinfo.value)

    assert get_address(web3_pp, "Ocean") == "0x1234567890123456789012345678901234567890"


@enforce_types
def test_condition_sapphire_keys():
    assert _condition_sapphire_keys({}) == {}

    assert _condition_sapphire_keys({"foo": "bar"}) == {"foo": "bar"}

    k1 = {"oasis_saphire_testnet": "test", "oasis_saphire": "main", "foo": "bar"}
    k2 = {
        "oasis_saphire_testnet": "test",
        "oasis_saphire": "main",
        "sapphire-testnet": "test",
        "sapphire-mainnet": "main",
        "foo": "bar",
    }
    assert _condition_sapphire_keys(k1) == k2

    k3 = {"sapphire-testnet": "test", "sapphire-mainnet": "main", "foo": "bar"}
    assert _condition_sapphire_keys(k3) == k3
