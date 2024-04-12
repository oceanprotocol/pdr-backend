import ccxt
from enforce_typing import enforce_types

from pdr_backend.ppss.exchange_mgr_ss import ExchangeMgrSS
from pdr_backend.exchange.mock_exchange import MockExchange


@enforce_types
class ExchangeMgr:
    """
    An interface class for making trades on exchanges
    (Other classes read data from exchanges)

    This class wraps interfaces of exchanges:
    - ccxt
    - Mock exchange, for testing
    - dydx (soon)
    """

    def __init__(self, ss: ExchangeMgrSS):
        self.ss = ss

    def exchange(self, exchange_str: str):
        """
        @description
          Return an exchange object, determined by its name and whether mocking

        @arguments
          exchange_str -- eg "mock", "binance", "binanceus", "kraken", "dydx"

        @return
          <one of: MockExchange, ccxt.binance.binance, ..>

        @notes
          ccxt docs (including py):
            https://docs.ccxt.com/#/

          ccxt.binance implementation:
            https://github.com/ccxt/ccxt/blob/master/python/ccxt/binance.py

          example usage:
            https://blog.adnansiddiqi.me/getting-started-with-ccxt-crypto-exchange-library-and-python/
        """
        if exchange_str == "mock":
            # ccxt has a "sandbox mode" but that requires more API keys.
            # It's easier to just have our own simple mock.
            return MockExchange()

        if exchange_str == "dydx":
            raise NotImplementedError()

        exchange_class = getattr(ccxt, exchange_str)  # eg ccxt.binance
        exchange = exchange_class(self.ss.ccxt_params)  # eg ccxt.binance(params)
        return exchange
