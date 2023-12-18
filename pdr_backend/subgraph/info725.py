from typing import Dict, Optional, Union
from enforce_typing import enforce_types
from web3 import Web3


@enforce_types
def key_to_key725(key: str):
    key725 = Web3.keccak(key.encode("utf-8")).hex()
    return key725


@enforce_types
def value_to_value725(value: Union[str, None]):
    if value is None:
        value725 = None
    else:
        value725 = Web3.to_hex(text=value)
    return value725


@enforce_types
def value725_to_value(value725) -> Union[str, None]:
    if value725 is None:
        value = None
    else:
        value = Web3.to_text(hexstr=value725)
    return value


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
        if key in info_keys:
            value = info[key]
        else:
            value = None
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
