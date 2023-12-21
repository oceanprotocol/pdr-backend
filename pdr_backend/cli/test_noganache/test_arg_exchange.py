import pytest
from enforce_typing import enforce_types

from pdr_backend.cli.arg_exchange import ArgExchanges


@enforce_types
def test_pack_exchange_str_list():
    assert str(ArgExchanges([])) == ""
    assert str(ArgExchanges(["binance"])) == "binance"
    assert str(ArgExchanges(["binance", "kraken"])) == "binance,kraken"

    with pytest.raises(TypeError):
        ArgExchanges("")

    with pytest.raises(TypeError):
        ArgExchanges(None)

    with pytest.raises(TypeError):
        ArgExchanges("")

    with pytest.raises(ValueError):
        ArgExchanges(["adfs"])

    with pytest.raises(ValueError):
        ArgExchanges(["binance fgds"])


@enforce_types
def test_verify_exchange_str():
    # ok
    strs = [
        "binance",
        "kraken",
    ]
    for exchange_str in strs:
        ArgExchanges([exchange_str])

    # not ok
    strs = [
        "",
        "  ",
        "xyz",
    ]
    for exchange_str in strs:
        with pytest.raises(ValueError):
            ArgExchanges([exchange_str])
