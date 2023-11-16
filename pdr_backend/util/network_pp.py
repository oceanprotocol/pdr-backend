from enforce_typing import enforce_types

from pdr_backend.util.strutil import StrMixin


class NetworkPP(StrMixin):
    @enforce_types
    def __init__(self, network:str, d: dict):
        self.network = network # e.g. "sapphire-testnet", "sapphire-mainnet"
        self.d = d  # yaml_dict["data_pp"]

    @property
    def dn(self) -> str: # "d at network". Compact on purpose.
        return self.d[self.network]
    
    @property
    def address_file(self) -> str:
        return self.dn["address_file"]

    @property
    def rpc_url(self) -> str:
        return self.dn["rpc_url"]

    @property
    def subgraph_url(self) -> str:
        return self.dn["subgraph_url"]

    @property
    def stake_token(self) -> str:
        return self.dn["stake_token"]

    @property
    def owner_addrs(self) -> str:
        return self.dn["owner_addrs"]
