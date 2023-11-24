from pdr_backend.util.constants import (
    SAPPHIRE_MAINNET_CHAINID,
    SAPPHIRE_TESTNET_CHAINID,
)
from pdr_backend.util.constants_opf_addrs import get_opf_addresses


def test_get_opf_addresses_testnet():
    # sapphire testnet
    addrs = get_opf_addresses(SAPPHIRE_TESTNET_CHAINID)
    assert len(addrs) > 3
    assert "dfbuyer" in addrs
    assert "websocket" in addrs
    assert "trueval" in addrs


def test_get_opf_addresses_mainnet():
    # sapphire testnet
    addrs = get_opf_addresses(SAPPHIRE_MAINNET_CHAINID)
    assert len(addrs) > 3
    assert "dfbuyer" in addrs
    assert "websocket" in addrs
    assert "trueval" in addrs
