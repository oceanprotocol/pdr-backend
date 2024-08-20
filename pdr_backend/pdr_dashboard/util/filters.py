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


@enforce_types
def table_column_range_condition(
    item, field, min_value: Optional[str], max_value: Optional[str]
):
    item_value = float(item[field])
    min_value = min_value or ""
    max_value = max_value or ""

    if min_value and item_value < float(min_value):
        return False

    if max_value and item_value > float(max_value):
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
