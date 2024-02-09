from typing import Dict, List, Optional

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

    @property
    def min_bal(self) -> Optional[int]:
        return self.d.get("min_bal", None)

    @property
    def topup_bal(self) -> Optional[int]:
        return self.d.get("topup_bal", None)

    def all_topup_addresses(self, network) -> Dict[str, str]:
        addresses: Dict[str, str] = {}

        if "opf_addresses" in self.addresses:
            addresses = get_opf_addresses(network)

        for i, address in enumerate(self.addresses):
            if address == "opf_addresses":
                continue

            addresses[str(i)] = address

        return addresses

    def get_min_bal(self, token, addr_label) -> int:
        if self.min_bal is not None:
            return self.min_bal

        if token.name == "ROSE":
            return 250 if addr_label == "dfbuyer" else 30

        return 0 if addr_label in ["trueval", "dfbuyer"] else 20

    def get_topup_bal(self, token, addr_label) -> int:
        if self.topup_bal is not None:
            return self.topup_bal

        if token.name == "ROSE":
            return 250 if addr_label == "dfbuyer" else 30

        return 0 if addr_label in ["trueval", "dfbuyer"] else 20
