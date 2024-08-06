from enforce_typing import enforce_types
from numerize import numerize
from typing import Union


@enforce_types
def format_metric(metric: Union[int, float], value_id: str) -> str:
    match value_id:
        case "feeds_page_Accuracy_metric" | "accuracy_metric":
            return format_accuracy(float(metric))
        case "feeds_page_Volume_metric" | "feeds_page_Revenue_metric":
            return format_ocean_amount(int(metric))
        case "profit_metric" | "stake_metric":
            return format_decimal_ocean_amount(float(metric))
        case "costs_metric":
            return f"~{format_decimal_ocean_amount(float(metric))}"
        case _:
            return metric


@enforce_types
def format_table(
    rows: list[dict[str, Union[int, float]]], columns: list[dict[str, str]]
) -> list[dict[str, str]]:
    """
    Format table rows.
    Args:
        rows (list[dict[str, Union[int, float]]): Table rows.
        columns (list[dict[str, str]]): Table columns.
    Returns:
        list[dict[str, str]]: Formatted table rows.
    """

    return [
        {
            column["id"]: format_column(row[column["id"]], column["id"])
            for column in columns
        }
        for row in rows
    ]


@enforce_types
def format_column(value: Union[int, float, str], column_id: str) -> str:
    match column_id:
        case "addr":
            return format_addr(value)
        case "avg_accuracy":
            return format_accuracy(float(value))
        case "sales_revenue_(OCEAN)" | "volume_(OCEAN)":
            return format_ocean_amount(int(value), w_suffix=False)
        case "avg_stake_(OCEAN)":
            return f"~{format_decimal_ocean_amount(float(value), w_suffix=False)}"
        case _:
            return value


@enforce_types
def format_addr(addr: str) -> str:
    """
    Format address.
    Args:
        addr (str): Address.
    Returns:
        str: Formatted address.
    """

    return f"{addr[:5]}...{addr[-5:]}"


@enforce_types
def format_ocean_amount(amount: int, w_suffix: bool = True) -> str:
    """
    Format Ocean date.
    Args:
        amount (int): Ocean amount.
    Returns:
        str: Formatted Ocean amount.
    """

    return f"{numerize.numerize(amount,2)}{" OCEAN" if w_suffix else ""}"


@enforce_types
def format_decimal_ocean_amount(amount: float, w_suffix: bool = True) -> str:
    """
    Format Ocean date.
    Args:
        amount (float): Ocean amount.
    Returns:
        str: Formatted Ocean amount.
    """

    return f"{round(amount, 2)}{" OCEAN" if w_suffix else ""}"


@enforce_types
def format_accuracy(accuracy: float) -> str:
    """
    Format accuracy.
    Args:
        accuracy (float): Accuracy.
    Returns:
        str: Formatted accuracy.
    """

    return f"{round(accuracy, 2)}%"
