from typing import Union

from enforce_typing import enforce_types
from numerize import numerize

PREDICTOORS_HOME_PAGE_TABLE_COLS = [
    {"name": "User Address", "id": "addr"},
    {"name": "User", "id": "full_addr"},
    {"name": "Profit", "id": "total_profit"},
    {"name": "Accuracy", "id": "avg_accuracy"},
    {"name": "Stake", "id": "avg_stake"},
]

FEEDS_HOME_PAGE_TABLE_COLS = [
    {"name": "Pair", "id": "pair"},
    {"name": "Source", "id": "source"},
    {"name": "Timeframe", "id": "timeframe"},
    {"name": "Full Addr", "id": "contract"},
    {"name": "Accuracy", "id": "avg_accuracy"},
    {"name": "Sales", "id": "sales"},
]

FEEDS_TABLE_COLS = [
    {"name": "Addr", "id": "addr"},
    {"name": "Base Token", "id": "base_token"},
    {"name": "Quote Token", "id": "quote_token"},
    {"name": "Source", "id": "source"},
    {"name": "Timeframe", "id": "timeframe"},
    {"name": "Full Addr", "id": "full_addr"},
    {"name": "Accuracy", "id": "avg_accuracy"},
    {"name": "Avg Stake Per Epoch (Ocean)", "id": "avg_stake"},
    {"name": "Volume (Ocean)", "id": "volume"},
    {"name": "Price (Ocean)", "id": "price"},
    {"name": "Sales", "id": "sales_str"},
    {"name": "Sales Raw", "id": "sales"},
    {"name": "Sales Revenue (Ocean)", "id": "sales_revenue"},
    {"name": "hidden_df", "id": "df_buy_count"},
    {"name": "hidden_ws", "id": "ws_buy_count"},
]

PREDICTOORS_TABLE_COLS = [
    {"name": "Addr", "id": "addr"},
    {"name": "Apr", "id": "apr"},
    {"name": "Full Addr", "id": "full_addr"},
    {"name": "Accuracy", "id": "avg_accuracy"},
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

    if "sales" in columns and "df_buy_count" in columns and "ws_buy_count" in columns:
        df["sales_str"] = (
            df.apply(
                lambda x: format_sales_info_data(
                    x.sales, x.df_buy_count, x.ws_buy_count
                ),
                axis=1,
            )
            if not df.empty
            else ""
        )

    for column in columns:
        # pylint: disable=cell-var-from-loop
        if column == "sales_str":
            continue
        df[column] = df[column].apply(lambda x: format_value(x, column))

    return df


@enforce_types
def format_sales_info_data(total, df_buy, ws_buy) -> str:
    total_str = format_currency(total, suffix="", show_decimal=False)

    df_buy_str = (
        f"{format_currency(df_buy, suffix="", show_decimal=False)} DF"
        if df_buy > 0
        else ""
    )
    ws_buy_str = (
        f"{format_currency(ws_buy, suffix="", show_decimal=False)} WS"
        if ws_buy > 0
        else ""
    )
    sales_info = ""

    if df_buy_str or ws_buy_str:
        sales_info = ", ".join(filter(None, [df_buy_str, ws_buy_str]))
        sales_info = f" ({sales_info})"

    return total_str + sales_info


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
