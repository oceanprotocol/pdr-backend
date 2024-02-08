import copy
import os
import pytest

from enforce_typing import enforce_types
from pdr_backend.util.constants_opf_addrs import get_opf_addresses

from pdr_backend.ppss.topup_ss import TopupSS


_D = {"addresses": ["default"]}


@enforce_types
def test_topup_ss():
    ss = TopupSS(_D)
    assert ss.addresses == ["default"]
    assert ss.all_topup_addresses("sapphire-testnet") == get_opf_addresses(
        "sapphire-testnet"
    )

    D2 = copy.deepcopy(_D)
    D2["addresses"] = ["0x1", "0x2"]

    ss = TopupSS(D2)
    assert len(ss.addresses) == 2
    assert len(ss.all_topup_addresses("sapphire-testnet")) == 2

    D3 = copy.deepcopy(_D)
    D3["addresses"] = ["default", "0x1", "0x2"]

    ss = TopupSS(D3)
    assert len(ss.addresses) == 3
    assert (
        len(ss.all_topup_addresses("sapphire-testnet"))
        == len(get_opf_addresses("sapphire-testnet")) + 2
    )
