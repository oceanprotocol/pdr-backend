from pathlib import Path

from enforce_typing import enforce_types
import pytest

from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.ppss.web3_pp import del_network_override
from pdr_backend.util.contract import (
    get_address,
    get_addresses,
    get_contract_abi,
    get_contract_filename,
    _condition_sapphire_keys,
)

_NETWORKS = [
    "sapphire-testnet",
    "sapphire-mainnet",
    "development",
]


@enforce_types
@pytest.mark.parametrize("network", _NETWORKS)
def test_contract_main(network, monkeypatch):
    # setup
    del_network_override(monkeypatch)
    ppss = mock_ppss("5m", ["binance BTC/USDT c"], network)
    web3_pp = ppss.web3_pp
    assert web3_pp.network == network

    # tests
    assert get_address(web3_pp, "Ocean") is not None

    assert get_addresses(web3_pp) is not None

    result = get_contract_abi("ERC20Template3", web3_pp.address_file)
    assert len(result) > 0 and isinstance(result, list)

    result = get_contract_filename("ERC20Template3", web3_pp.address_file)
    assert result is not None and isinstance(result, Path)


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
