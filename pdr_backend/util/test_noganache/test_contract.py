from pathlib import Path

import pytest
from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.util.contract import (
    _condition_sapphire_keys,
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

    ppss = mock_ppss(
        [{"predict": "binance BTC/USDT c 5m", "train_on": "binance BTC/USDT c 5m"}],
        network,
    )
    web3_pp = ppss.web3_pp
    assert web3_pp.network == network

    result = web3_pp.get_contract_abi("ERC20Template3")
    assert len(result) > 0 and isinstance(result, list)

    result = get_contract_filename("ERC20Template3", web3_pp.address_file)
    assert result is not None and isinstance(result, Path)

    with pytest.raises(TypeError):
        web3_pp.get_contract_abi("xyz")


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
