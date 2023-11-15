import ccxt
from enforce_typing import enforce_types


@enforce_types
def test_ccxt_mexc_pairs():
    exchange = ccxt.mexc3()
    markets = exchange.load_markets()

    # print(f"MEXC symbols: {[v.get('symbol','') for k,v in exchange.markets.items()]}")

    tokens = [v.get("base", "") for k, v in markets.items()]
    assert len(tokens) > 0

    usdc_tokens = [v for k, v in markets.items() if v.get("settle", None) == "USDC"]
    assert len(usdc_tokens) == 0

    # Find unique settle tokens
    settle_tokens = [v.get("settle", "") for k, v in markets.items()]
    unique_settle_tokens = []
    for token in settle_tokens:
        if token not in unique_settle_tokens:
            unique_settle_tokens.append(token)
    assert len(unique_settle_tokens) > 1

    # print("MEXC unique_settle: ", unique_settle_tokens)


@enforce_types
class MockBinance:
    def __init__(self):
        self.markets = {
            "BTC/USDT": {"symbol": "BTC/USDT", "base": "BTC", "settle": "USDT"},
            "ETH/USDT": {"symbol": "ETH/USDT", "base": "ETH", "settle": "USDT"},
            "ETH/USDC": {"symbol": "ETH/USDC", "base": "ETH", "settle": "USDC"},
            # Add more market data here as needed
        }

    def load_markets(self):
        return self.markets


@enforce_types
def test_ccxt_binance_pairs():
    exchange = MockBinance()
    markets = exchange.load_markets()

    # print(f"BNB symbols: {[v.get('symbol','') for k,v in exchange.markets.items()]}")

    tokens = [v.get("base", "") for k, v in markets.items()]
    assert len(tokens) > 0

    usdc_tokens = [v for k, v in markets.items() if v.get("settle", None) == "USDC"]
    assert len(usdc_tokens) == 1

    # Find unique settle tokens
    settle_tokens = [v.get("settle", "") for k, v in markets.items()]
    unique_settle_tokens = []
    for token in settle_tokens:
        if token not in unique_settle_tokens:
            unique_settle_tokens.append(token)
    assert len(unique_settle_tokens) > 1

    # print("BNB unique_quotes: ", unique_settle_tokens)
