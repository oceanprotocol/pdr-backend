from enforce_typing import enforce_types


@enforce_types
def recursive_update(d, u):
    for k, v in u.items():
        if isinstance(v, dict) and k in d and isinstance(d[k], dict):
            recursive_update(d[k], v)
        else:
            d[k] = v


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
    (key, val) = [i for i in d.items()][0]  # pylint: disable=unnecessary-comprehension
    return (key, val)
