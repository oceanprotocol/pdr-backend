from enforce_typing import enforce_types
import pytest

from pdr_backend.util.exchangestr import (
    pack_exchange_str_list,
    verify_exchange_str,
)


@enforce_types
def test_pack_exchange_str_list():
    assert pack_exchange_str_list(None) is None
    assert pack_exchange_str_list([]) is None
    assert pack_exchange_str_list(["binance"]) == "binance"
    assert pack_exchange_str_list(["binance", "kraken"]) == "binance,kraken"

    with pytest.raises(TypeError):
        pack_exchange_str_list("")

    with pytest.raises(ValueError):
        pack_exchange_str_list(["adfs"])

    with pytest.raises(ValueError):
        pack_exchange_str_list(["binance fgds"])


@enforce_types
def test_verify_exchange_str():
    # ok
    strs = [
        "binance",
        "kraken",
    ]
    for exchange_str in strs:
        verify_exchange_str(exchange_str)

    # not ok
    strs = [
        "",
        "  ",
        "xyz",
    ]
    for exchange_str in strs:
        with pytest.raises(ValueError):
            verify_exchange_str(exchange_str)
