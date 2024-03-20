import ccxt
from enforce_typing import enforce_types

from pdr_backend.ppss import ExchangeMgrSS


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

    def __init__(self, ss: ExchangeSS):
        self.ss = ExchangeSS

    def exchange(self, name: str):
        """
        @description
          Return an exchange object, determined by its name and whether mocking

        @arguments
          name -- eg "mock", "binance", "binanceus", "kraken", "dydx"

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
        if name == "mock":
            # ccxt has a "sandbox mode" but that requires more API keys.
            # It's easier to just have our own simple mock.
            return MockExchange()

        if name == "dydx":
            raise NotImplementedError()

        exchange_class = getattr(ccxt, name)  # eg ccxt.binance
        exchange = exchange_class(**self.ss.ccxt_params)  # eg ccxt.binance(**params)
        return exchange
