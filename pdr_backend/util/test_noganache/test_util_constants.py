import numpy as np
from enforce_typing import enforce_types

from pdr_backend.util.constants import (
    CAND_SIGNALS,
    CAND_TIMEFRAMES,
    CAND_USDCOINS,
    CHAR_TO_SIGNAL,
    S_PER_DAY,
    S_PER_MIN,
    SAPPHIRE_MAINNET_CHAINID,
    SAPPHIRE_MAINNET_RPC,
    SAPPHIRE_TESTNET_CHAINID,
    SAPPHIRE_TESTNET_RPC,
    SUBGRAPH_MAX_TRIES,
    WEB3_MAX_TRIES,
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
    assert "close" in CAND_SIGNALS
    assert len(CAND_SIGNALS) == 5
    assert CHAR_TO_SIGNAL["c"] == "close"
    assert set(CHAR_TO_SIGNAL.values()) == set(CAND_SIGNALS)
