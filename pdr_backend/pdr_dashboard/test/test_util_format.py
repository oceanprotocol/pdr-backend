import polars as pl

from pdr_backend.pdr_dashboard.util.format import (
    format_approximate_currency_with_decimal_val,
    format_column,
    format_currency_val,
    format_eth_address,
    format_percentage,
    format_percentage_val,
    format_value,
)


def test_format_eth_address():
    df = pl.DataFrame(
        {
            "address": [
                "0x1234567890123456789012345678901234567890",
                "0x123456789012345678901234567890123456789",
                "",
            ]
        }
    )

    result = format_eth_address(df, "address")
    assert result["address"][0] == "0x123...67890"
    assert result["address"][1] == "0x123...56789"
    assert result["address"][2] == "No address"


def test_format_currency():
    df = pl.DataFrame(
        {
            "avg_stake": [1234567890.1234567890, -10.01, 0.0],
        }
    )
    assert format_column(df, "avg_stake")["avg_stake"][0] == "1.23B"
    assert format_column(df, "avg_stake")["avg_stake"][1] == "-10.01"
    assert format_column(df, "avg_stake")["avg_stake"][2] == "0"

    assert format_currency_val(1234567890.1234567890) == "1.23B OCEAN"
    assert (
        format_currency_val(1234567890.1234567890, show_decimal=True)
        == "1234567890.12 OCEAN"
    )
    assert format_currency_val(1234567890.1234567890, suffix=" OCEAN") == "1.23B OCEAN"
    assert (
        format_currency_val(1234567890.1234567890, suffix=" OCEAN", show_decimal=True)
        == "1234567890.12 OCEAN"
    )


def test_format_percentage():
    df = pl.DataFrame(
        {
            "percentage": [1.0, 12.0, 12.345],
        }
    )

    result = format_percentage(df, "percentage")
    assert result["percentage"][0] == "1.0%"
    assert result["percentage"][1] == "12.0%"
    assert result["percentage"][2] == "12.35%"

    assert format_percentage_val(1) == "1.0%"
    assert format_percentage_val(12) == "12.0%"
    assert format_percentage_val(12.345) == "12.35%"


def test_format_approximate_currency_with_decimal():
    assert (
        format_approximate_currency_with_decimal_val(1234567890.1234567890)
        == "~1234567890.12"
    )
    assert format_approximate_currency_with_decimal_val(1234567890) == "~1234567890"


def test_format_value():
    assert format_value(12.0, "feeds_page_Accuracy_metric") == "12.0%"
    assert format_value(1.12, "accuracy_metric") == "1.12%"
    assert format_value(12, "feeds_page_Volume_metric") == "12 OCEAN"
    assert format_value(12, "feeds_page_Revenue_metric") == "12 OCEAN"
    assert format_value(9876.12, "profit_metric") == "9.88K OCEAN"
    assert format_value(9876.12, "stake_metric") == "9.88K OCEAN"
    assert format_value(9876, "costs_metric") == "~9876"
    assert format_value(12, "unknown") == "12"


def test_format_col():
    df = pl.DataFrame({"avg_accuracy": [12]})
    assert format_column(df, "avg_accuracy")["avg_accuracy"][0] == "12%"

    df = pl.DataFrame({"sales_revenue": [9876.12]})
    assert format_column(df, "sales_revenue")["sales_revenue"][0] == "9.88K"

    df = pl.DataFrame({"volume": [9876543]})
    assert format_column(df, "volume")["volume"][0] == "9.88M"

    df = pl.DataFrame({"avg_stake": [12.0]})
    assert format_column(df, "avg_stake")["avg_stake"][0] == "12"

    df = pl.DataFrame({"unknown": [12]})
    assert format_column(df, "unknown")["unknown"][0] == "12"
