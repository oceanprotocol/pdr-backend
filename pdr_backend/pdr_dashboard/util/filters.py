from typing import Optional
from enforce_typing import enforce_types
from dash import callback_context


@enforce_types
def filter_table_by_range(
    min_val: Optional[str], max_val: Optional[str], label_text: str
):
    min_val = min_val or ""
    max_val = max_val or ""

    ctx = callback_context
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id in [
        "clear_feeds_filters_button",
        "clear_predictoors_filters_button",
    ] or (not min_val and not max_val):
        return label_text

    return f"{label_text} {min_val}-{max_val}"


def table_column_filter_condition(item, field, values):
    return not values or item[field] in values


def table_search_condition(item, search_value):
    if not search_value:
        return True
    search_value = search_value.lower()
    return any(
        search_value in item.get(key, "").lower()
        for key in ["addr", "base_token", "quote_token"]
    )


def _float_repr(value):
    try:
        return float(value)
    except ValueError:
        pass

    denumerized = _denumerize(value)
    if denumerized != "err":
        return float(denumerized)

    return value


# copied directly from numerize.py, unreleased in a package
def _denumerize(n):
    try:
        sufixes = [
            "",
            "K",
            "M",
            "B",
            "T",
            "Qa",
            "Qu",
            "S",
            "Oc",
            "No",
            "D",
            "Ud",
            "Dd",
            "Td",
            "Qt",
            "Qi",
            "Se",
            "Od",
            "Nd",
            "V",
            "Uv",
            "Dv",
            "Tv",
            "Qv",
            "Qx",
            "Sx",
            "Ox",
            "Nx",
            "Tn",
            "Qa",
            "Qu",
            "S",
            "Oc",
            "No",
            "D",
            "Ud",
            "Dd",
            "Td",
            "Qt",
            "Qi",
            "Se",
            "Od",
            "Nd",
            "V",
            "Uv",
            "Dv",
            "Tv",
            "Qv",
            "Qx",
            "Sx",
            "Ox",
            "Nx",
            "Tn",
            "x",
            "xx",
            "xxx",
            "X",
            "XX",
            "XXX",
            "END",
        ]

        sci_expr = [
            1e0,
            1e3,
            1e6,
            1e9,
            1e12,
            1e15,
            1e18,
            1e21,
            1e24,
            1e27,
            1e30,
            1e33,
            1e36,
            1e39,
            1e42,
            1e45,
            1e48,
            1e51,
            1e54,
            1e57,
            1e60,
            1e63,
            1e66,
            1e69,
            1e72,
            1e75,
            1e78,
            1e81,
            1e84,
            1e87,
            1e90,
            1e93,
            1e96,
            1e99,
            1e102,
            1e105,
            1e108,
            1e111,
            1e114,
            1e117,
            1e120,
            1e123,
            1e126,
            1e129,
            1e132,
            1e135,
            1e138,
            1e141,
            1e144,
            1e147,
            1e150,
            1e153,
            1e156,
            1e159,
            1e162,
            1e165,
            1e168,
            1e171,
            1e174,
            1e177,
        ]

        suffix_idx = 0

        for i in n:
            if not isinstance(i, int):
                suffix_idx = n.index(i)

        suffix = n[suffix_idx:]
        num = n[:suffix_idx]

        suffix_val = sci_expr[sufixes.index(suffix)]
        result = int(num) * suffix_val

        return result
    except:  # pylint: disable=bare-except
        return "err"


@enforce_types
def table_column_range_condition(
    item, field, min_value: Optional[str], max_value: Optional[str]
):
    item_value = float(item[field])
    min_value = min_value or ""
    max_value = max_value or ""

    if min_value and item_value < _float_repr(min_value):
        return False

    if max_value and item_value > _float_repr(max_value):
        return False

    return True


def check_condition(item, condition_type, field, *values):
    if field and field.startswith("p_"):
        field = field[2:]

    if condition_type == "filter":
        return table_column_filter_condition(item, field, values[0])

    if condition_type == "range":
        return table_column_range_condition(
            item,
            field,
            values[0],
            values[1],
        )

    if condition_type == "search":
        return table_search_condition(item, values[0])

    return True
