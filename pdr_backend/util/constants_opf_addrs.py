from typing import Dict

from enforce_typing import enforce_types


@enforce_types
def get_opf_addresses(network_name: str) -> Dict[str, str]:
    if network_name == "sapphire-testnet":
        return {
            "predictoor1": "0xE02A421dFc549336d47eFEE85699Bd0A3Da7D6FF",
            "predictoor2": "0x00C4C993e7B0976d63E7c92D874346C3D0A05C1e",
            "predictoor3": "0x005C414442a892077BD2c1d62B1dE2Fc127E5b9B",
            "trueval": "0x005FD44e007866508f62b04ce9f43dd1d36D0c0c",
            "websocket": "0x008d4866C4071AC9d74D6359604762C7B581D390",
            "dfbuyer": "0xeA24C440eC55917fFa030C324535fc49B42c2fD7",
        }

    if network_name == "sapphire-mainnet":
        return {
            "predictoor20": "0x784b52987A894d74E37d494F91eD03a5Ab37aB36",
            "predictoor21": "0x74c52ce6c26780B78140D183596F6a8Dfa135BE3",
            "trueval": "0x886A892670A7afc719Dcf36eF92c798203F74B67",
            "websocket": "0x6Cc4Fe9Ba145AbBc43227b3D4860FA31AFD225CB",
            "dfbuyer": "0x2433e002Ed10B5D6a3d8d1e0C5D2083BE9E37f1D",
        }

    raise ValueError(network_name)
