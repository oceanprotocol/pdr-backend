from enforce_typing import enforce_types

from pdr_backend.exchange.constants import (
    BASE_URL_DYDX,
    TIMEFRAME_TO_DYDX_RESOLUTION,
)


@enforce_types
def test_exchange_constants():
    assert "https" in BASE_URL_DYDX
    
    assert isinstance(TIMEFRAME_TO_DYDX_RESOLUTION, dict)
    assert "5m" in TIMEFRAME_TO_DYDX_RESOLUTION
    
