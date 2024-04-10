from typing import List, Union

import ccxt
from enforce_typing import enforce_types


@enforce_types
class ArgExchange:
    def __init__(self, exchange_str: str):
        
        if not exchange_str:
            raise ValueError(exchange_str)
        
        if not (exchange_str == "dydx" or hasattr(ccxt, exchange_str)):
            raise ValueError(exchange_str)

        self.exchange = exchange_str

    def __str__(self):
        return self.exchange

    def __eq__(self, other):
        return self.exchange == str(other)

    def __hash__(self):
        return hash(self.exchange)

    
# Subscripted generics cannot be used with class and instance checks
# Therefore don't have @enforce_types here
class ArgExchanges(List[ArgExchange]):
    def __init__(self, exchange_str_list: Union[List[str], List[ArgExchange]]):
        if not isinstance(exchange_str_list, list):
            raise TypeError("exchange_str_list must be a list")

        arg_exchange_list = [ArgExchange(str(exchange)) for exchange in exchange_str_list if exchange]

        if not arg_exchange_list:
            raise ValueError(exchange_str_list)

        super().__init__(arg_exchange_list)

    def __str__(self):
        return ",".join([str(exchange) for exchange in self])


@enforce_types
def verify_exchange_str(exchange_str: str):
    """Raises an error if exchange_str not ok"""
    _ = ArgExchange(exchange_str)
