import ccxt
from os import getenv

# ====================================================================
# test ccxt exchange


def test_ccxt_mexc_pairs():
    exchange = ccxt.mexc({})
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


def test_ccxt_binance_pairs():
    exchange = ccxt.binance({})
    markets = exchange.load_markets()

    # print(f"BNB symbols: {[v.get('symbol','') for k,v in exchange.markets.items()]}")

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

    # print("BNB unique_quotes: ", unique_settle_tokens)
