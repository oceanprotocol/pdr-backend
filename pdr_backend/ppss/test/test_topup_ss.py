import copy
from unittest.mock import Mock

from enforce_typing import enforce_types

from pdr_backend.ppss.topup_ss import TopupSS
from pdr_backend.util.constants_opf_addrs import get_opf_addresses

_D = {"addresses": ["opf_addresses"]}


@enforce_types
def test_topup_ss():
    ss = TopupSS(_D)
    assert ss.addresses == ["opf_addresses"]
    assert ss.all_topup_addresses("sapphire-testnet") == get_opf_addresses(
        "sapphire-testnet"
    )

    D2 = copy.deepcopy(_D)
    D2["addresses"] = ["0x1", "0x2"]

    ss = TopupSS(D2)
    assert len(ss.addresses) == 2
    assert len(ss.all_topup_addresses("sapphire-testnet")) == 2

    D3 = copy.deepcopy(_D)
    D3["addresses"] = ["opf_addresses", "0x1", "0x2"]

    ss = TopupSS(D3)
    assert len(ss.addresses) == 3
    assert (
        len(ss.all_topup_addresses("sapphire-testnet"))
        == len(get_opf_addresses("sapphire-testnet")) + 2
    )

    OCEAN = Mock()
    OCEAN.name = "OCEAN"
    ROSE = Mock()
    ROSE.name = "ROSE"

    assert ss.get_min_bal(OCEAN, "0") == 20
    assert ss.get_min_bal(OCEAN, "dfbuyer") == 0
    assert ss.get_min_bal(ROSE, "dfbuyer") == 250
    assert ss.get_topup_bal(ROSE, "dfbuyer") == 250


@enforce_types
def test_topup_ss_bals():
    ss = TopupSS({"addresses": ["opf_addresses"], "min_bal": 100, "topup_bal": 200})

    OCEAN = Mock()
    OCEAN.name = "OCEAN"
    ROSE = Mock()
    ROSE.name = "ROSE"

    assert ss.get_min_bal("OCEAN", "0") == 100
    assert ss.get_min_bal("OCEAN", "dfbuyer") == 100
    assert ss.get_topup_bal("ROSE", "dfbuyer") == 200
