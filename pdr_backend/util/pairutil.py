from enforce_typing import enforce_types


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
