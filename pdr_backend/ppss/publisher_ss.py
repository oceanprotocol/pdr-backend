from enforce_typing import enforce_types
from pdr_backend.util.strutil import StrMixin


class PublisherSS(StrMixin):
    @enforce_types
    def __init__(self, network: str, d: dict):
        self.d = d  # yaml_dict["publisher_ss"]
        self.network = network  # e.g. "sapphire-testnet", "sapphire-mainnet"

    # --------------------------------
    # yaml properties
    @property
    def fee_collector_address(self) -> str:
        """
        Returns the address of FeeCollector of the current network
        """
        return self.d[self.network]["fee_collector_address"]
