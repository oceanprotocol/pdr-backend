import pytest
from enforce_typing import enforce_types

from pdr_backend.cli.arg_exchange import (
    ArgExchange,
    ArgExchanges,
    verify_exchange_str,
)


@enforce_types
def test_arg_exchange__happy_path():
    arg_exchange1 = ArgExchange("binance")
    assert arg_exchange1.exchange_str == "binance"
    assert str(arg_exchange1) == "binance"

    arg_exchange2 = ArgExchange("binance")
    assert arg_exchange1 == arg_exchange2

    arg_exchange3 = ArgExchange("kraken")
    assert arg_exchange1 != arg_exchange3

    _ = ArgExchange("dydx")


@enforce_types
def test_arg_exchange__bad_path():
    with pytest.raises(TypeError):
        _ = ArgExchange(None)

    with pytest.raises(TypeError):
        _ = ArgExchange(3.2)

    with pytest.raises(ValueError):
        _ = ArgExchange("")

    with pytest.raises(ValueError):
        _ = ArgExchange("  ")

    with pytest.raises(ValueError):
        _ = ArgExchange("not_an_exchange")


@enforce_types
def test_arg_exchanges__happy_path():
    assert str(ArgExchanges(["binance"])) == "binance"
    assert str(ArgExchanges(["kraken"])) == "kraken"
    assert str(ArgExchanges(["binance", "kraken"])) == "binance,kraken"


@enforce_types
def test_arg_exchanges__bad_path():
    with pytest.raises(TypeError):
        ArgExchanges("")

    with pytest.raises(TypeError):
        ArgExchanges(None)

    with pytest.raises(TypeError):
        ArgExchanges("")

    with pytest.raises(ValueError):
        ArgExchanges([])

    with pytest.raises(ValueError):
        ArgExchanges(["adfs"])

    with pytest.raises(ValueError):
        ArgExchanges(["binance fgds"])


@enforce_types
def test_verify_exchange_str__happy_path():
    verify_exchange_str("binance")
    verify_exchange_str("kraken")
    verify_exchange_str("dydx")


@enforce_types
def test_exchange_str_ok__bad_path():
    for bad_val in ["", " ", "foo"]:
        with pytest.raises(ValueError):
            verify_exchange_str(bad_val)

    for bad_val in [None, 3, 3.2]:
        with pytest.raises(TypeError):
            verify_exchange_str(bad_val)
