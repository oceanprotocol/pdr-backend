from pdr_backend.pdr_dashboard.util.format import (
    format_eth_address,
    format_currency,
    format_percentage,
    format_currency_with_decimal,
    format_currency_with_decimal_and_suffix,
    format_approximate_currency_with_decimal,
    format_value,
)


def test_format_eth_address():
    assert (
        format_eth_address("0x1234567890123456789012345678901234567890")
        == "0x123...67890"
    )
    assert (
        format_eth_address("0x123456789012345678901234567890123456789")
        == "0x123...56789"
    )


def test_format_eth_address_empty():
    assert format_eth_address("") == "No address"


def test_format_currency():
    assert format_currency(1234567890.1234567890) == "1.23B OCEAN"
    assert (
        format_currency(1234567890.1234567890, show_decimal=True)
        == "1234567890.12 OCEAN"
    )
    assert format_currency(1234567890.1234567890, suffix=" OCEAN") == "1.23B OCEAN"
    assert (
        format_currency(1234567890.1234567890, suffix=" OCEAN", show_decimal=True)
        == "1234567890.12 OCEAN"
    )


def test_format_percentage():
    assert format_percentage(1) == "1.0%"
    assert format_percentage(12) == "12.0%"
    assert format_percentage(12.345) == "12.35%"


def test_format_currency_with_decimal():
    assert format_currency_with_decimal(1234567890.1234567890) == "1234567890.12"
    assert format_currency_with_decimal(1234567890) == "1234567890"


def test_format_currency_with_decimal_and_suffix():
    assert (
        format_currency_with_decimal_and_suffix(1234567890.1234567890)
        == "1234567890.12 OCEAN"
    )
    assert format_currency_with_decimal_and_suffix(1234567890) == "1234567890 OCEAN"


def test_format_approximate_currency_with_decimal():
    assert (
        format_approximate_currency_with_decimal(1234567890.1234567890)
        == "~1234567890.12"
    )
    assert format_approximate_currency_with_decimal(1234567890) == "~1234567890"


def test_format_value():
    assert format_value(12.0, "feeds_page_Accuracy_metric") == "12.0%"
    assert format_value(1.12, "accuracy_metric") == "1.12%"
    assert format_value(12, "feeds_page_Volume_metric") == "12 OCEAN"
    assert format_value(12, "feeds_page_Revenue_metric") == "12 OCEAN"
    assert format_value(9876.12, "profit_metric") == "9.88K OCEAN"
    assert format_value(9876.12, "stake_metric") == "9.88K OCEAN"
    assert format_value(9876, "costs_metric") == "~9876"
    assert (
        format_value("0x1234567890123456789012345678901234567890", "addr")
        == "0x123...67890"
    )
    assert format_value(12.0, "avg_accuracy") == "12.0%"
    assert format_value(9876.12, "sales_revenue_(OCEAN)") == "9.88K"
    assert format_value(9876543, "volume_(OCEAN)") == "9.88M"
    assert format_value(12.0, "avg_stake_per_epoch_(OCEAN)") == "12.0"
    assert format_value(12, "unknown") == "12"
