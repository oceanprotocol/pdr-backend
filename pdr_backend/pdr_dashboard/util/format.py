from typing import Union

from enforce_typing import enforce_types
from numerize import numerize

FORMAT_CONFIG = {
    "feeds_page_Accuracy_metric": "percentage",
    "accuracy_metric": "percentage",
    "feeds_page_Volume_metric": "currency",
    "feeds_page_Revenue_metric": "currency",
    "profit_metric": "currency_with_decimal_and_suffix",
    "stake_metric": "currency_with_decimal_and_suffix",
    "costs_metric": "avg_currency_with_decimal",
    "addr": "eth_address",
    "avg_accuracy": "percentage",
    "sales_revenue_(OCEAN)": "currency_with_decimal",
    "volume_(OCEAN)": "currency_with_decimal",
    "avg_stake_(OCEAN)": "avg_currency_with_decimal",
}


@enforce_types
def format_value(value: Union[int, float, str], value_id: str) -> str:
    """
    Format value.
    Args:
        value (Union[int, float]): Value.
        value_id (str): Value id.
    Returns:
        str: Formatted value.
    """
    if value_id in FORMAT_CONFIG:
        return globals()["format_" + FORMAT_CONFIG[value_id]](value)
    return str(value)


@enforce_types
def format_table(
    rows: list[dict[str, Union[int, float]]], columns: list[dict[str, str]]
) -> list[dict[str, str]]:
    """
    Format table rows.
    Args:
        rows (list[dict[str, Union[int, float]]]): Table rows.
        columns (list[dict[str, str]]): Table columns.
    Returns:
        list[dict[str, str]]: Formatted table rows.
    """
    return [
        {
            column["id"]: format_value(row[column["id"]], column["id"])
            for column in columns
        }
        for row in rows
    ]


@enforce_types
def format_eth_address(address: str) -> str:
    """
    Shorten ethereum address.
    Args:
        address (str): Address.
    Returns:
        str: Formatted address.
    """
    return f"{address[:5]}...{address[-5:]}"


@enforce_types
def format_currency(
    amount: Union[float, int], suffix: str = " OCEAN", show_decimal: bool = False
) -> str:
    """
    Format Ocean amount.
    Args:
        amount (float): Ocean amount.
    Returns:
        str: Formatted Ocean amount.
    """
    formatted_amount = f"{round(amount, 2)}" if show_decimal else numerize.numerize(amount)
    return f"{formatted_amount}{suffix}"


@enforce_types
def format_percentage(accuracy: Union[float, int]) -> str:
    """
    Format accuracy.
    Args:
        accuracy (float): Accuracy.
    Returns:
        str: Formatted accuracy.
    """
    return f"{round(float(accuracy), 2)}%"


@enforce_types
def format_currency_with_decimal(value: Union[float, int]) -> str:
    return format_currency(value, suffix="", show_decimal=True)


@enforce_types
def format_currency_with_decimal_and_suffix(value: Union[float, int]) -> str:
    return format_currency(value, suffix=" OCEAN", show_decimal=True)


@enforce_types
def format_avg_currency_with_decimal(value: Union[float, int]) -> str:
    return f"~{format_currency(value, suffix="", show_decimal=True)}"
