#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import Dict, Optional, Union

from enforce_typing import enforce_types
from web3 import Web3

from pdr_backend.util.constants import WHITELIST_FEEDS_MAINNET


@enforce_types
def key_to_key725(key: str):
    return Web3.keccak(key.encode("utf-8")).hex()


@enforce_types
def value_to_value725(value: Union[str, None]):
    return None if value is None else Web3.to_hex(text=value)


@enforce_types
def value725_to_value(value725) -> Union[str, None]:
    return None if value725 is None else Web3.to_text(hexstr=value725)


@enforce_types
def info_to_info725(info: Dict[str, Union[str, None]]) -> list:
    """
    @arguments
      info -- eg {
        "pair": "ETH/USDT",
        "timeframe": "5m",
        "source": None,
        "extra1" : "extra1_value",
        "extra2" : None,
      }
      where info may/may not have keys for "pair", "timeframe", source"
      and may have extra keys

    @return
      info725 -- eg [
        {"key":encoded("pair"), "value":encoded("ETH/USDT")},
        {"key":encoded("timeframe"), "value":encoded("5m") },
        ...
      ]
      Where info725 may or may not have each of these keys:
        "pair", "timeframe", "source"
    """
    keys = ["pair", "timeframe", "source"]
    info_keys = list(info.keys())
    for info_key in info_keys:
        if info_key not in keys:
            keys.append(info_key)

    info725 = []
    for key in keys:
        value = None if key not in info_keys else info[key]
        key725 = key_to_key725(key)
        value725 = value_to_value725(value)
        info725.append({"key": key725, "value": value725})

    return info725


@enforce_types
def info725_to_info(info725: list) -> Dict[str, Optional[str]]:
    """
    @arguments
      info725 -- eg [{"key":encoded("pair"), "value":encoded("ETH/USDT")},
                          {"key":encoded("timeframe"), "value":encoded("5m") },
                           ... ]
      where info725 may/may not have keys for "pair", "timeframe", source"
      and may have extra keys

    @return
      info -- e.g. {"pair": "ETH/USDT",
                         "timeframe": "5m",
                         "source": None}
      where info always has keys "pair", "timeframe", "source"
    """
    info: Dict[str, Optional[str]] = {}
    target_keys = ["pair", "timeframe", "source"]
    for key in target_keys:
        info[key] = None
        for item725 in info725:
            key725, value725 = item725["key"], item725["value"]
            if key725 == key_to_key725(key):
                value = value725_to_value(value725)
                info[key] = value
                break

    return info


def get_pair_timeframe_source_from_contract(contract):
    if contract["token"]["nft"]:
        info725 = contract["token"]["nft"]["nftData"]
        info = info725_to_info(info725)  # {"pair": "ETH/USDT", }
        pair = info["pair"]
        timeframe = info["timeframe"]
        source = info["source"]
        return (pair, timeframe, source)

    if contract["id"] in WHITELIST_FEEDS_MAINNET:
        pair = contract["token"]["name"]
        timeframe = "5m" if int(contract["secondsPerEpoch"]) == 300 else "1h"
        source = "binance"  # true for all mainnet contracts
        return (pair, timeframe, source)

    raise Exception(f"Could not get pair, timeframe, source from contract: {contract}")
