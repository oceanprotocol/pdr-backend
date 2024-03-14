from typing import List

from enforce_typing import enforce_types

@enforce_types
def recursive_update(d, u):
    for k, v in u.items():
        if isinstance(v, dict) and k in d and isinstance(d[k], dict):
            recursive_update(d[k], v)
        else:
            d[k] = v

@enforce_types   
def dict_in_dictlist(d: dict, dictlist: List[dict]) -> bool:
    """Return True if dict d is in dictlist"""
    for dict_i in dictlist:
        if d == dict_i:
            return True
    return False

@enforce_types
def keyval(d: dict) -> tuple:
    """
    @description
       Compact routine to extract the key & value from a single-item dict.
    
    @arguments
      d -- dict with just 1 item

    @return
      key - key of dict's only item
      value - value ""
    """
    if len(d) != 1:
        raise ValueError((len(d), d))
    (key, val) = [i for i in d.items()][0]
    return (key, val)

