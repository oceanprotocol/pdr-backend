from enforce_typing import enforce_types
import pytest

from pdr_backend.util.timeframestr import (
    pack_timeframe_str_list,
    verify_timeframe_str,
)


@enforce_types
def test_pack_timeframe_str_list():
    assert pack_timeframe_str_list(None) is None
    assert pack_timeframe_str_list([]) is None
    assert pack_timeframe_str_list(["1h"]) == "1h"
    assert pack_timeframe_str_list(["1h", "5m"]) == "1h,5m"

    with pytest.raises(TypeError):
        pack_timeframe_str_list("")

    with pytest.raises(ValueError):
        pack_timeframe_str_list(["adfs"])

    with pytest.raises(ValueError):
        pack_timeframe_str_list(["1h fgds"])


@enforce_types
def test_verify_timeframe_str():
    verify_timeframe_str("1h")
    verify_timeframe_str("1m")

    with pytest.raises(ValueError):
        verify_timeframe_str("foo")
