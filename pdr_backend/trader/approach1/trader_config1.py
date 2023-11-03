from enforce_typing import enforce_types
from os import getenv
from pdr_backend.trader.trader_config import TraderConfig

CAND_EXCHANGE = ["mexc3", "mexc"]
CAND_PAIR = [
    "BTC/USDT",
    "ETH/USDT",
    "ADA/USDT",
    "BNB/USDT",
    "SOL/USDT",
    "XRP/USDT",
    "DOT/USDT",
    "LTC/USDT",
    "DOGE/USDT",
    "TRX/USDT",
]
CAND_TIMEFRAME = ["5m", "1h"]


# Mexc3 does not support
@enforce_types
class TraderConfig1(TraderConfig):
    def __init__(self):
        super().__init__()

        self.exchange_id = getenv("EXCHANGE_FILTER")
        self.pair = getenv("PAIR_FILTER")
        self.timeframe = getenv("TIMEFRAME_FILTER")

        ## Exchange Parameters
        self.exchange_pair = (
            getenv("EXCHANGE_PAIR_FILTER")
            if getenv("EXCHANGE_PAIR_FILTER")
            else self.pair
        )

        ## Position Parameters
        self.size = getenv("POSITION_SIZE")

        assert self.exchange_id in CAND_EXCHANGE, "Exchange must be valid"
        assert self.pair in CAND_PAIR, "Pair must be valid"
        assert self.timeframe in CAND_TIMEFRAME, "Timeframe must be valid"
        assert (
            self.size != None and self.size > 0.0
        ), "Position size must be greater than 0.0"
