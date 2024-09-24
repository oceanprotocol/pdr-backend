from typing import Union
import polars as pl

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

FORMAT_COLS_CONFIG = {
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
}

FORMAT_VALUES_CONFIG = {
    "feeds_page_Accuracy_metric": "percentage",
    "accuracy_metric": "percentage",
    "feeds_page_Volume_metric": "currency",
    "feeds_page_Revenue_metric": "currency",
    "feeds_page_Sales_metric": "currency_without_decimal",
    "profit_metric": "currency_without_decimal_with_suffix",
    "stake_metric": "currency_without_decimal_with_suffix",
    "costs_metric": "approximate_currency_with_decimal",
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
    if value_id not in FORMAT_VALUES_CONFIG:
        return str(value)

    return globals()["format_" + FORMAT_VALUES_CONFIG[value_id] + "_val"](value)


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
        df = format_sales_info_data(df)

    for col in columns:
        if col == "sales_str":
            continue

        if col not in FORMAT_COLS_CONFIG:
            df = df.with_columns(pl.col(col).cast(pl.String).alias(col))
            continue

        func_name = globals()["format_" + FORMAT_COLS_CONFIG[col]]
        df = func_name(df, col)
        continue

    return df


# TODO: typing
@enforce_types
def format_eth_address(df, col):
    return df.with_columns(
        pl.when(pl.col(col).str.len_chars() > 0)
        .then(pl.col(col).str.slice(0, 5) + "..." + pl.col(col).str.slice(-5))
        .otherwise(pl.lit("No address"))
        .alias(col)
    )


@enforce_types
def format_percentage(df, col):
    return df.with_columns(
        (pl.col(col).round(2).cast(pl.String) + pl.lit("%")).alias(col)
    )


@enforce_types
def format_sales_info_data(df) -> str:
    if df.is_empty():
        return df.with_columns(pl.col("sales_str").alias("sales_str"))

    total = format_currency(df, "sales", suffix="", show_decimal=False)["sales"]
    df_buy = format_currency(df, "df_buy_count", suffix=" DF", show_decimal=False)["df_buy_count"]
    ws_buy = format_currency(df, "ws_buy_count", suffix=" WS", show_decimal=False)["ws_buy_count"]

    df2 = df.with_columns(
        pl.when(pl.col("df_buy_count") > 0).then(df_buy).otherwise(pl.lit("")).alias("df_buy_str"),
        pl.when(pl.col("ws_buy_count") > 0).then(ws_buy).otherwise(pl.lit("")).alias("ws_buy_str")
    )

    df2 = df2.with_columns(
        (
            total +
            pl.lit(" (") +
            (pl.col("df_buy_str") + ", " + pl.col("ws_buy_str")).str.strip_chars_start(", ").str.strip_chars_end(", ") +
            pl.lit(")")
        ).alias("sales_info")
    )

    return df.with_columns(df2["sales_info"].alias("sales_str"))


@enforce_types
def format_currency(
    df, col, base=None, suffix: str = " OCEAN", show_decimal: bool = False, prefix=""
):
    """
    Format Ocean amount.
    Args:
        amount (float): Ocean amount.
    Returns:
        str: Formatted Ocean amount.
    """
    if base is None:
        base = (
            pl.col(col).round(2).cast(pl.String)
            if show_decimal
            else pl.col(col).map_elements(numerize.numerize, return_dtype=pl.String)
        )

    return df.with_columns((pl.lit(prefix) + base + pl.lit(suffix)).alias(col))


@enforce_types
def format_currency_conditional(df, col) -> str:
    base = (
        pl.when(pl.col(col).is_in([-1000, 1000]))
        .then(pl.col(col).round(2).cast(pl.String))
        .otherwise(pl.col(col).map_elements(numerize.numerize, return_dtype=pl.String))
    )

    return format_currency(df, col, base, suffix="")


@enforce_types
def format_currency_without_decimal(df, col):
    return format_currency(df, col, suffix="", show_decimal=False)


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
    return format_currency(value, suffix="", show_decimal=True, prefix="~")


@enforce_types
def format_currency_val(
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
def format_currency_without_decimal_val(amount: Union[float, int]) -> str:
    return format_currency_val(amount, suffix="", show_decimal=False)


@enforce_types
def format_currency_without_decimal_with_suffix_val(amount: Union[float, int]) -> str:
    return format_currency_val(amount, suffix=" OCEAN", show_decimal=False)


@enforce_types
def format_currency_with_decimal_val(value: Union[float, int]) -> str:
    return format_currency_val(value, suffix="", show_decimal=True)


@enforce_types
def format_currency_with_decimal_and_suffix_val(value: Union[float, int]) -> str:
    return format_currency_val(value, suffix=" OCEAN", show_decimal=True)


@enforce_types
def format_approximate_currency_with_decimal_val(value: Union[float, int]) -> str:
    formatted_value = format_currency_val(value, suffix="", show_decimal=True)
    return f"~{formatted_value}"


@enforce_types
def format_currency_conditional_val(amount: Union[float, int]) -> str:
    show_decimal = False
    if -1000 < amount < 1000:
        show_decimal = True

    return format_currency_val(amount, suffix="", show_decimal=show_decimal)


@enforce_types
def format_percentage_val(accuracy: Union[float, int]) -> str:
    """
    Format accuracy.
    Args:
        accuracy (float): Accuracy.
    Returns:
        str: Formatted accuracy.
    """
    return f"{round(float(accuracy), 2)}%"
