from typing import Dict, List

from enforce_typing import enforce_types

from pdr_backend.util.strutil import StrMixin
from pdr_backend.util.constants_opf_addrs import get_opf_addresses


@enforce_types
class TopupSS(StrMixin):
    __STR_OBJDIR__ = ["d"]

    def __init__(self, d: dict):
        self.d = d  # yaml_dict["sim_ss"]

    # --------------------------------
    # properties direct from yaml dict
    @property
    def addresses(self) -> List[str]:
        return self.d["addresses"]

    def all_topup_addresses(self, network) -> str:
        addresses: Dict[str, str] = {}

        if "default" in self.addresses:
            addresses = get_opf_addresses(network)

        for i, address in enumerate(self.addresses):
            if address == "default":
                continue

            addresses[i] = address

        return addresses
