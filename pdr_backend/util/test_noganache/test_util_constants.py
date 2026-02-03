import numpy as np
from enforce_typing import enforce_types

from pdr_backend.util.constants import (
    CAND_TIMEFRAMES,
    CAND_USDCOINS,
    CHAR_TO_SIGNAL,
    DFREWARDS_ADDR,
    S_PER_DAY,
    S_PER_MIN,
    SAPPHIRE_MAINNET_CHAINID,
    SAPPHIRE_MAINNET_RPC,
    SAPPHIRE_TESTNET_CHAINID,
    SAPPHIRE_TESTNET_RPC,
    SUBGRAPH_MAX_TRIES,
    USDC_TOKEN_ADDR,
    WEB3_MAX_TRIES,
    WROSE_TOKEN_ADDR,
    ZERO_ADDRESS,
)


@enforce_types
def test_util_constants():
    assert ZERO_ADDRESS[:3] == "0x0"

    assert "https://" in SAPPHIRE_TESTNET_RPC
    assert isinstance(SAPPHIRE_TESTNET_CHAINID, int)
    assert "https://" in SAPPHIRE_MAINNET_RPC
    assert isinstance(SAPPHIRE_MAINNET_CHAINID, int)

    assert S_PER_MIN == 60
    assert S_PER_DAY == 86400

    assert 1 <= SUBGRAPH_MAX_TRIES <= np.inf
    assert isinstance(SUBGRAPH_MAX_TRIES, int)
    assert 1 <= WEB3_MAX_TRIES <= np.inf
    assert isinstance(WEB3_MAX_TRIES, int)

    assert "USDT" in CAND_USDCOINS
    assert "5m" in CAND_TIMEFRAMES
    assert "close" in CHAR_TO_SIGNAL.values()
    assert len(CHAR_TO_SIGNAL) == 5
    assert CHAR_TO_SIGNAL["c"] == "close"


@enforce_types
def test_payout_contract_addresses():
    """Test that payout contract addresses are valid checksummed Ethereum addresses."""
    # All addresses should start with 0x
    assert DFREWARDS_ADDR.startswith("0x")
    assert WROSE_TOKEN_ADDR.startswith("0x")
    assert USDC_TOKEN_ADDR.startswith("0x")

    # All addresses should be 42 characters (0x + 40 hex chars)
    assert len(DFREWARDS_ADDR) == 42
    assert len(WROSE_TOKEN_ADDR) == 42
    assert len(USDC_TOKEN_ADDR) == 42

    # Verify specific expected addresses on Sapphire Mainnet
    assert DFREWARDS_ADDR == "0xc37F8341Ac6e4a94538302bCd4d49Cf0852D30C0"
    assert WROSE_TOKEN_ADDR == "0x8Bc2B030b299964eEfb5e1e0b36991352E56D2D3"
    assert USDC_TOKEN_ADDR == "0x2c2E3812742Ab2DA53a728A09F5DE670Aba584b6"
