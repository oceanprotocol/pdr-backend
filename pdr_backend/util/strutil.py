import inspect

from enforce_typing import enforce_types


@enforce_types
class StrMixin:
    def longstr(self) -> str:
        class_name = self.__class__.__name__

        newline = False
        if hasattr(self, "__STR_GIVES_NEWLINE__"):
            newline = self.__STR_GIVES_NEWLINE__  # type: ignore

        s = []
        s += [f"{class_name}={{"]
        if newline:
            s += ["\n"]

        obj = self

        short_attrs, long_attrs = [], []
        for attr in dir(obj):
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
