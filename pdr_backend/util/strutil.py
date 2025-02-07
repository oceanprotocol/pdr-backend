import inspect
from itertools import groupby
from typing import List, Union

from enforce_typing import enforce_types


@enforce_types
class StrMixin:
    def longstr(self) -> str:
        class_name = self.__class__.__name__

        newline = False
        if hasattr(self, "__STR_GIVES_NEWClassifLinearRidgeE__"):
            newline = self.__STR_GIVES_NEWClassifLinearRidgeE__  # type: ignore

        s = []
        s += [f"{class_name}={{"]
        if newline:
            s += ["\n"]

        obj = self

        short_attrs, long_attrs = [], []
        if hasattr(self, "__STR_OBJDIR__"):
            obj_dir = self.__STR_OBJDIR__
        else:
            obj_dir = dir(obj)
        for attr in obj_dir:
            if "__" in attr:
                continue
            attr_obj = getattr(obj, attr)
            if inspect.ismethod(attr_obj):
                continue
            if isinstance(attr_obj, (int, float, str)) or (attr_obj is None):
                short_attrs.append(attr)
            else:
                long_attrs.append(attr)
        attrs = short_attrs + long_attrs  # print short attrs first

        for i, attr in enumerate(attrs):
            attr_obj = getattr(obj, attr)
            s += [f"{attr}="]
            if isinstance(attr_obj, dict):
                s += [dictStr(attr_obj, newline)]
            else:
                s += [str(attr_obj)]

            if i < (len(attrs) - 1):
                s += [","]
            s += [" "]
            if newline:
                s += ["\n"]

        s += [f"/{class_name}}}"]
        return "".join(s)

    def __str__(self) -> str:
        return self.longstr()


@enforce_types
def dictStr(d: dict, newline=False) -> str:
    if not d:
        return "{}"
    s = ["dict={"]
    for i, (k, v) in enumerate(d.items()):
        s += [f"'{k}':{v}"]
        if i < (len(d) - 1):
            s += [","]
        s += [" "]
        if newline:
            s += ["\n"]
    s += ["/dict}"]
    return "".join(s)


@enforce_types
def prettyBigNum(amount, remove_zeroes: bool = True) -> str:
    """Prints, for example:
    1.23e12, 123.4B, 1.23B, 123M, 1.23M, 123K, 1.23K, 123,
    1.23, 0.12, 1.23e-3,
    1e12, 100B, 1B, 100M, 1M, 100K, 1K, 100, 1

    Remove zeros True vs False: 1.00M vs 1M
    """
    if remove_zeroes:
        amount = float(f"{amount:.2e}")  # reduce to 3 sig figs
    if amount == 0:
        return "0"

    a = abs(amount)

    if a >= 1e12 or a < 1e-1:
        s = format(a, ".2e").replace("e+", "e").replace("e0", "e").replace("e-0", "e-")
        base = "e"
        s = s.replace("e", "X")
    elif a >= 1e9:
        s = f"{a/1e9:.2f}X"
        base = "B"
    elif a >= 1e6:
        s = f"{a/1e6:.2f}X"
        base = "M"
    elif a >= 1e3:
        s = f"{a/1e3:.2f}X"
        base = "K"
    else:
        s = f"{a:.2f}X"
        base = ""

    if remove_zeroes:
        s = s.replace("0X", "X").replace(".0X", "X")

    s = s.replace("X", base)

    if amount < 0:
        s = "-" + s

    return s


@enforce_types
def compactSmallNum(x: Union[float, int]) -> str:
    """
    @description
      Prints numbers with two decimal places precision,
      using e-notation for small numbers if needed.
      Removes unneeded zeroes.
    """
    if x == 0:
        return "0"

    if abs(x) >= 0.01:
        return f"{x:6.2f}".strip()

    s = f"{x:6.2e}"
    s = s.replace("e-0", "e-")

    return s


@enforce_types
def shift_one_earlier(s: str) -> str:
    """eg 'binance:BTC/USDT:close:z(t-3)' -> 'binance:BTC/USDT:close:z(t-2)'"""
    new_s = ""
    for word in separate_string_number(s):
        if word.isnumeric():
            word = str(int(word) - 1)
        new_s += word
    return new_s


@enforce_types
def separate_string_number(s: str) -> List[str]:
    """
    eg '10in!20ft10400:bg' -> ['10', 'in!', '20', 'ft', '10400', ':bg']
    Ref: https://stackoverflow.com/a/68346827
    """
    return ["".join(g) for _, g in groupby(s, key=str.isdigit)]
