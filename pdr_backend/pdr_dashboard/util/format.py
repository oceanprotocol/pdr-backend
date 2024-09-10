from typing import Any, Dict, List, Union

from enforce_typing import enforce_types
from numerize import numerize

PREDICTOORS_HOME_PAGE_TABLE_COLS = [
    {"name": "User Address", "id": "addr"},
    {"name": "User", "id": "full_addr"},
    {"name": "Accuracy", "id": "avg_accuracy"},
    {"name": "Profit", "id": "total_profit"},
    {"name": "Stake", "id": "avg_stake"},
]

FEEDS_HOME_PAGE_TABLE_COLS = [
    {"name": "Pair", "id": "pair"},
    {"name": "Source", "id": "source"},
    {"name": "Timeframe", "id": "timeframe"},
    {"name": "Full Addr", "id": "contract"},
]

FEEDS_TABLE_COLS = [
    {"name": "Addr", "id": "addr"},
    {"name": "Base Token", "id": "base_token"},
    {"name": "Quote Token", "id": "quote_token"},
    {"name": "Source", "id": "source"},
    {"name": "Timeframe", "id": "timeframe"},
    {"name": "Full Addr", "id": "full_addr"},
    {"name": "Avg Accuracy", "id": "avg_accuracy"},
    {"name": "Avg Stake Per Epoch (Ocean)", "id": "avg_stake"},
    {"name": "Volume (Ocean)", "id": "volume"},
    {"name": "Price (Ocean)", "id": "price"},
    {"name": "Sales", "id": "sales_str"},
    {"name": "Sales Raw", "id": "sales_raw"},
    {"name": "Sales Revenue (Ocean)", "id": "sales_revenue"},
]

PREDICTOORS_TABLE_COLS = [
    {"name": "Addr", "id": "addr"},
    {"name": "Apr", "id": "apr"},
    {"name": "Full Addr", "id": "full_addr"},
    {"name": "Accuracy", "id": "accuracy"},
    {"name": "Number Of Feeds", "id": "feed_count"},
    {"name": "Staked (Ocean)", "id": "total_stake"},
    {"name": "Gross Income (Ocean)", "id": "gross_income"},
    {"name": "Stake Loss (Ocean)", "id": "stake_loss"},
    {"name": "Tx Costs (Ocean)", "id": "tx_costs_(OCEAN)"},
    {"name": "Net Income (Ocean)", "id": "net_income_(OCEAN)"},
]

FORMAT_CONFIG = {
    "feeds_page_Accuracy_metric": "percentage",
    "accuracy_metric": "percentage",
    "feeds_page_Volume_metric": "currency",
    "feeds_page_Revenue_metric": "currency",
    "feeds_page_Sales_metric": "currency_without_decimal",
    "profit_metric": "currency_without_decimal_with_suffix",
    "stake_metric": "currency_without_decimal_with_suffix",
    "costs_metric": "approximate_currency_with_decimal",
    "addr": "eth_address",
    "user": "eth_address",
    "avg_accuracy": "percentage",
    "avg_stake": "currency_conditional",
    "sales_str": "sales_info_data",
    "total_profit": "currency_without_decimal",
    "volume": "currency_without_decimal",
    "total_stake": "currency_conditional",
    "gross_income": "currency_conditional",
    "stake_loss": "currency_conditional",
    "tx_costs_(OCEAN)": "currency_conditional",
    "net_income_(OCEAN)": "currency_conditional",
    "sales_revenue": "currency_conditional",
    "apr": "percentage",
    "accuracy": "percentage",
    "predictoors_page_accuracy_metric": "percentage",
    "predictoors_page_staked_metric": "currency",
    "predictoors_page_gross_income_metric": "currency",
}


@enforce_types
def pick_from_dict(data: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
    """
    Pick keys from dictionary.
    Args:
        data (Dict[str, Any]): Data.
        keys (List[str]): Keys.
    Returns:
        Dict[str, Any]: Picked keys.
    """
    return {key: data[key] for key in keys}


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
def format_df(
    df,
) -> list[dict[str, str]]:
    """
    Format table rows.
    Args:
        rows (list[dict[str, Union[int, float]]]): Table rows.
        columns (list[dict[str, str]]): Table columns.
    Returns:
        list[dict[str, str]]: Formatted table rows.
    """
    columns = df.columns

    for column in columns:
        # pylint: disable=cell-var-from-loop
        df[column] = df[column].apply(lambda x: format_value(x, column))

    return df


@enforce_types
def format_sales_info_data(data: Union[str, int]) -> str:
    """
    Format sales multiple data.
    Args:
        data str: Sales data. eg: 2160_2140-DF_20-WS
    Returns:
        str: Formatted sales data. eg: 2.16K (2.14K DF, 20 WS)
    """
    splitted_data = str(data).split("_")

    result_data = []

    for _, item in enumerate(splitted_data):
        if item.isnumeric():
            result_data.append(
                format_currency(int(item), suffix="", show_decimal=False)
            )
        else:
            splitted_item = item.split("-")
            formatted_nr = format_currency(
                int(splitted_item[0]), suffix="", show_decimal=False
            )

            result_data.append(f"{formatted_nr} {splitted_item[1]}")

    info_part = (", ").join(result_data[1:])

    if info_part:
        info_part = f" ({info_part})"

    return result_data[0] + info_part


@enforce_types
def format_eth_address(address: str) -> str:
    """
    Shorten ethereum address.
    Args:
        address (str): Address.
    Returns:
        str: Formatted address.
    """
    if not address:
        return "No address"

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
    formatted_amount = (
        f"{round(amount, 2)}" if show_decimal else numerize.numerize(amount)
    )
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
def format_currency_conditional(amount: Union[float, int]) -> str:
    show_decimal = False
    if -1000 < amount < 1000:
        show_decimal = True

    return format_currency(amount, suffix="", show_decimal=show_decimal)


@enforce_types
def format_currency_without_decimal(amount: Union[float, int]) -> str:
    return format_currency(amount, suffix="", show_decimal=False)


@enforce_types
def format_currency_without_decimal_with_suffix(amount: Union[float, int]) -> str:
    return format_currency(amount, suffix=" OCEAN", show_decimal=False)


@enforce_types
def format_currency_with_decimal(value: Union[float, int]) -> str:
    return format_currency(value, suffix="", show_decimal=True)


@enforce_types
def format_currency_with_decimal_and_suffix(value: Union[float, int]) -> str:
    return format_currency(value, suffix=" OCEAN", show_decimal=True)


@enforce_types
def format_approximate_currency_with_decimal(value: Union[float, int]) -> str:
    formatted_value = format_currency(value, suffix="", show_decimal=True)
    return f"~{formatted_value}"
