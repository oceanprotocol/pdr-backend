from enforce_typing import enforce_types
from pdr_backend.util.number_formatter import NumberFormatter


@enforce_types
def test_format_currency():
    assert NumberFormatter.format_currency(0) == "$0.00"
    assert NumberFormatter.format_currency(0.0) == "$0.00"
    assert NumberFormatter.format_currency(1200) == "$1.20K"
    assert NumberFormatter.format_currency(123000) == "$123.00K"
    assert NumberFormatter.format_currency(1230000) == "$1.23M"
    assert NumberFormatter.format_currency(1230000000) == "$1.23B"

    assert (
        NumberFormatter.format_currency(num=1200, currency_symbol="£", decimal_places=1)
        == "£1.2K"
    )

    assert (
        NumberFormatter.format_currency(
            num=12300, currency_symbol="£", decimal_places=1
        )
        == "£12.3K"
    )


@enforce_types
def test_format_suffix():
    assert NumberFormatter.format_suffix(0) == "0.00"
    assert NumberFormatter.format_suffix(0.0) == "0.00"
    assert NumberFormatter.format_suffix(1200) == "1.20K"
    assert NumberFormatter.format_suffix(123000) == "123.00K"
    assert NumberFormatter.format_suffix(1230000) == "1.23M"
    assert NumberFormatter.format_suffix(1230000000) == "1.23B"

    assert NumberFormatter.format_suffix(num=1200, decimal_places=1) == "1.2K"

    assert NumberFormatter.format_suffix(num=12300, decimal_places=1) == "12.3K"

    assert NumberFormatter.format_suffix(num=123000, decimal_places=1) == "123.0K"


@enforce_types
def test_format_scientific():
    assert NumberFormatter.format_scientific(0) == "0.00e+00"
    assert NumberFormatter.format_scientific(1200) == "1.20e+03"
    assert NumberFormatter.format_scientific(123000) == "1.23e+05"
    assert NumberFormatter.format_scientific(1230000) == "1.23e+06"


@enforce_types
def test_format_locale():
    assert NumberFormatter.format_locale(0) == "0"
    assert NumberFormatter.format_locale(1200) == "1,200"
    assert NumberFormatter.format_locale(123000) == "123,000"
    assert NumberFormatter.format_locale(1230000) == "1,230,000"

    assert (
        NumberFormatter.format_locale(num=1230000, locale_code="de_DE") == "1.230.000"
    )

    assert (
        NumberFormatter.format_locale(num=1230000, locale_code="fr_FR") == "1 230 000"
    )

    assert (
        NumberFormatter.format_locale(num=1230000, locale_code="en_GB") == "1,230,000"
    )

    assert (
        NumberFormatter.format_locale(num=1230000, locale_code="en_US") == "1,230,000"
    )


@enforce_types
def test_with_instance():
    number_formatter = NumberFormatter(decimal_places=2)
    number_formatter.format(1200) == "1.20K"

    number_formatter = NumberFormatter(decimal_places=1, currency_symbol="€")
    number_formatter.format(4567) == "€4.5K"
