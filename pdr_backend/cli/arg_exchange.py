from typing import List, Union

import ccxt


class ArgExchange:
    def __init__(self, exchange: str):
        if not hasattr(ccxt, exchange):
            raise ValueError(exchange)

        self.exchange = exchange

    @property
    def exchange_class(self):
        return getattr(ccxt, self.exchange)

    def __str__(self):
        return self.exchange

    def __eq__(self, other):
        return self.exchange == str(other)

    def __hash__(self):
        return hash(self.exchange)


class ArgExchanges(List[ArgExchange]):
    def __init__(self, exchanges: Union[List[str], List[ArgExchange]]):
        if not isinstance(exchanges, list):
            raise TypeError("exchanges must be a list")

        super().__init__(
            [ArgExchange(str(exchange)) for exchange in exchanges if exchange]
        )

    def __str__(self):
        if not self:
            return ""

        return ",".join([str(exchange) for exchange in self])
