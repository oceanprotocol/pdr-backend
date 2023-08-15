from enforce_typing import enforce_types

from pdr_backend.utils.constants import (
    ZERO_ADDRESS,
    SAPPHIRE_TESTNET_RPC,
    SAPPHIRE_TESTNET_CHAINID,
    SAPPHIRE_MAINNET_RPC,
    SAPPHIRE_MAINNET_CHAINID,
)


@enforce_types
def test_constants1():
    assert ZERO_ADDRESS[:3] == "0x0"
    assert "https://" in SAPPHIRE_TESTNET_RPC
    assert isinstance(SAPPHIRE_TESTNET_CHAINID, int)
    assert "https://" in SAPPHIRE_MAINNET_RPC
    assert isinstance(SAPPHIRE_MAINNET_CHAINID, int)
