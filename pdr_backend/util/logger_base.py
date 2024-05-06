import abc
from typing import Union


class BaseLogLine(abc.ABC):
    def _compactNum(
        self, attr_or_amount: Union[float, str], use_eth: bool = False
    ) -> str:
        x = (
            getattr(self, attr_or_amount)
            if isinstance(attr_or_amount, str)
            else attr_or_amount
        )

        if use_eth:
            x = x.amt_eth

        if x < 0.01:
            return f"{x:6.2e}"

        return f"{x:6.2f}"
