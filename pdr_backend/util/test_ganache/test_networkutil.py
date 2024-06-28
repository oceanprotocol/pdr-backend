#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from enforce_typing import enforce_types

from pdr_backend.util.networkutil import (
    get_sapphire_postfix,
    get_subgraph_url,
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


def test_get_subgraph():
    expected = (
        "https://v4.subgraph.sapphire-testnet.oceanprotocol.com/"
        "subgraphs/name/oceanprotocol/ocean-subgraph"
    )
    assert get_subgraph_url("testnet") == expected

    with pytest.raises(ValueError):
        get_subgraph_url("sapphire-testnet")
