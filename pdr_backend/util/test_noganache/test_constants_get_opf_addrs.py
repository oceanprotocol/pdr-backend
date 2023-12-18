from enforce_typing import enforce_types
import pytest

from pdr_backend.util.constants_opf_addrs import get_opf_addresses


@enforce_types
def test_get_opf_addresses_testnet():
    addrs = get_opf_addresses("sapphire-testnet")
    assert len(addrs) > 3
    assert "dfbuyer" in addrs
    assert "websocket" in addrs
    assert "trueval" in addrs


@enforce_types
def test_get_opf_addresses_mainnet():
    # sapphire testnet
    addrs = get_opf_addresses("sapphire-mainnet")
    assert len(addrs) > 3
    assert "dfbuyer" in addrs
    assert "websocket" in addrs
    assert "trueval" in addrs


@enforce_types
def test_get_opf_addresses_other():
    for s in (
        "",
        "foo",
        "development",
        "oasis_saphire_testnet",
        "oasis_saphire",
    ):
        with pytest.raises(ValueError):
            get_opf_addresses(s)
