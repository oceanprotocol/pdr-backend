from pdr_backend.exchange.fetch_ohlcv_dydx import fetch_ohlcv_dydx
from pdr_backend.ppss.exchange_mgr_ss import ExchangeMgrSS


class DydxExchange:
    def __init__(self, ss: ExchangeMgrSS):
        self.ss = ss
        self.params = ss.dydx_params

    def fetch_ohlcv(self, pair_str: str, timeframe: str, since: str, limit: int):
        return fetch_ohlcv_dydx(pair_str, timeframe, since, limit)
