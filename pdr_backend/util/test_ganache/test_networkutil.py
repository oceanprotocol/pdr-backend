import pytest
from enforce_typing import enforce_types

from pdr_backend.util.networkutil import (
    get_sapphire_postfix,
)


@enforce_types
def test_get_sapphire_postfix():
    assert get_sapphire_postfix("sapphire-testnet"), "testnet"
    assert get_sapphire_postfix("sapphire-mainnet"), "mainnet"

    unwanteds = [
        "oasis_saphire_testnet",
        "saphire_mainnet",
        "barge-pytest",
        "barge-predictoor-bot",
        "development",
        "foo",
        "",
    ]
    for unwanted in unwanteds:
        with pytest.raises(ValueError):
            assert get_sapphire_postfix(unwanted)
