from typing import Union, List, Optional
import locale


class NumberFormatter:
    """
    A class for formatting numbers with suffixes for large values.
    The class can also format numbers as currency, in scientific notation,
    and according to the set locale.
    """

    # Static variable for suffixes
    suffixes = ["", "K", "M", "B", "T", "P", "E"]

    def __init__(
        self,
        decimal_places: int = 2,
        suffixes: Optional[List[str]] = None,
        locale_code: str = "en_US",
        currency_symbol=None,
    ):
        """
        Initializes the NumberFormatter with the given decimal places,
        suffixes, and locale.
        """
        self.decimal_places = decimal_places
        if suffixes:
            self.suffixes = suffixes
        self.locale_code = locale_code
        self.currency_symbol = currency_symbol

    def format(self, num: Union[float, int]) -> str:
        """
        Formats a number with suffixes for large values.
        The number is formatted with the set decimal places.

        Args:
            num: The number to format.

        Returns:
            The formatted number as a string.
        """
        if num == 0:
            return self._format_with_decimals(num)

        is_negative = num < 0
        num = abs(num)

        for i, suffix in enumerate(self.suffixes):
            unit = 1000 ** (i + 1)
            if num < unit:
                formatted_num = num / (unit / 1000)
                formatted_str = f"{formatted_num:.{self.decimal_places}f}{suffix}"
                return f"-{formatted_str}" if is_negative else formatted_str

        formatted_str = f"{num:.{self.decimal_places}f}"
        formatted_str_with_sign = f"-{formatted_str}" if is_negative else formatted_str
        local_str = locale_change(formatted_str_with_sign, self.locale_code)
        return f"{self.currency_symbol}{local_str}"

    @staticmethod
    def format_currency(
        num: Union[float, int], currency_symbol: str = "$", decimal_places: int = 2
    ) -> str:
        """
        Formats a number as currency.
        The number is formatted with the specified decimal places.

        Args:
            num: The number to format.
            currency_symbol: The symbol of the currency.
            decimal_places: The number of decimal places.

        Returns:
            The formatted number as a string.
        """
        formatted_number = NumberFormatter.format_suffix(
            num, decimal_places=decimal_places
        )
        integer_part, decimal_part = formatted_number.split(".")
        decimal_part = decimal_part.ljust(decimal_places, "0")
        return f"{currency_symbol}{integer_part}.{decimal_part}"

    @staticmethod
    def format_scientific(num: Union[float, int], decimal_places: int = 2) -> str:
        """
        Formats a number in scientific notation.
        The number is formatted with the specified decimal places.

        Args:
            num: The number to format.
            decimal_places: The number of decimal places.

        Returns:
            The formatted number as a string.
        """
        return f"{num:.{decimal_places}e}"

    @staticmethod
    def format_locale(
        num: Union[float, int], decimal_places: int = 0, locale_code: str = "en_US"
    ) -> str:
        """
        Formats a number according to the specified locale.
        The number is formatted with the specified decimal places.

        Args:
            num: The number to format.
            decimal_places: The number of decimal places.
            locale_str: The locale string.

        Returns:
            The formatted number as a string.
        """
        formatted_number = f"{num:,.{decimal_places}f}"

        return locale_change(formatted_number, locale_code)

    @staticmethod
    def format_suffix(num: Union[float, int], decimal_places: int = 2) -> str:
        """
        Static method to format a number with suffixes for large values.

        Args:
            num: The number to format.
            decimal_places: The number of decimal places.

        Returns:
            The formatted number as a string.
        """
        if num == 0:
            return f"{num:.{decimal_places}f}"

        is_negative = num < 0
        num = abs(num)

        for i, suffix in enumerate(NumberFormatter.suffixes):
            unit = 1000 ** (i + 1)
            if num < unit:
                formatted_num = num / (unit / 1000)
                formatted_str = f"{formatted_num:.{decimal_places}f}{suffix}"
                return f"-{formatted_str}" if is_negative else formatted_str

        formatted_str = f"{num:.{decimal_places}f}"
        return f"-{formatted_str}" if is_negative else formatted_str

    def _format_with_decimals(self, num: Union[float, int]) -> str:
        """Helper method to format a number with fixed decimal places."""
        return f"{num:.{self.decimal_places}f}"


def locale_change(formatted_number: str, locale_code: str) -> str:
    if locale_code == "fr_FR":
        return formatted_number.replace(",", " ").replace(".", ",")
    elif locale_code == "de_DE":
        return formatted_number.replace(",", " ").replace(".", ",").replace(" ", ".")
    elif locale_code in ["en-GB", "en_US"]:
        return formatted_number
    return formatted_number
