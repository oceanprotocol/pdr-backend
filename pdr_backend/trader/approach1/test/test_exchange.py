import ccxt
from os import getenv

# ====================================================================
# test ccxt exchange

def test_ccxt_mexc_pairs():
    exchange = ccxt.mexc({})
    markets = exchange.load_markets()

    tokens = [v.get('base','') for k,v in markets.items()]
    assert len(tokens) > 0

    print("MEXC tokens: ", tokens)

    usdc_tokens = [v for k,v in markets.items() if v.get('settle', None) == 'USDC']
    assert len(usdc_tokens) == 0
    
def test_ccxt_binance_pairs():
    exchange = ccxt.binance({})
    markets = exchange.load_markets()

    tokens = [v.get('base','') for k,v in markets.items()]
    assert len(tokens) > 0
    
    print(f"BNB tokens: {tokens}")
    
    usdc_tokens = [v for k,v in markets.items() if v.get('settle', None) == 'USDC']
    assert len(usdc_tokens) == 0