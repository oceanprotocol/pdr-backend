import os

from enforce_typing import enforce_types

from pdr_backend.util.strutil import StrMixin


@enforce_types
class TradeParams(StrMixin):
    def __init__(
        self,
        fee_percent: float,  # Eg 0.001 is 0.1%. Trading fee (simulated)
        init_holdings: dict,  # Eg {"USDT": 100000.00}
    ):
        self.fee_percent = fee_percent
        self.init_holdings = init_holdings


@enforce_types
class TradeSS(StrMixin):
    def __init__(self, do_plot: bool, logpath: str, buy_amt_usd: float):
        assert os.path.exists(logpath)

        self.do_plot = do_plot
        self.logpath = logpath  # directory, not file
        self.buy_amt_usd = buy_amt_usd


@enforce_types
def pairstr(coin: str, usdcoin: str) -> str:
    """Eg given 'BTC','USDT', return 'BTC/USDT'"""
    return f"{coin}/{usdcoin}"


@enforce_types
def pairstr_to_coin(pair: str) -> str:
    """Eg given 'BTC/USDT', return 'BTC'"""
    return pair.split("/")[0]


@enforce_types
def pairstr_to_usdcoin(pair: str) -> str:
    """Eg given 'BTC/USDT', return 'USDT'"""
    return pair.split("/")[1]
