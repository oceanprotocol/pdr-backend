import ccxt
from pdr_backend.models.contract_data import ContractData
from pdr_backend.trueval.trueval_config import TruevalConfig
from pdr_backend.trueval.trueval_agent import TruevalAgent

def get_true_val(
    topic: ContractData, initial_timestamp, end_timestamp
) -> Tuple[bool, bool]:
    """Given a topic, Returns the true val between end_timestamp and initial_timestamp
    Topic object looks like:

    {
        "name":"ETH-USDT",
        "address":"0x54b5ebeed85f4178c6cb98dd185067991d058d55",
        "symbol":"ETH-USDT",
        "blocks_per_epoch":"60",
        "blocks_per_subscription":"86400",
        "pair":"eth-usdt",
        "base":"eth",
        "quote":"usdt",
        "source":"kraken",
        "timeframe":"5m"
    }

    """
    symbol = topic.pair
    if topic.source == "binance" or topic.source == "kraken":
        symbol = symbol.replace("-", "/")
        symbol = symbol.upper()
    try:
        exchange_class = getattr(ccxt, topic.source)
        exchange_ccxt = exchange_class()
        price_initial = exchange_ccxt.fetch_ohlcv(
            symbol, "1m", since=initial_timestamp, limit=1
        )
        price_end = exchange_ccxt.fetch_ohlcv(
            symbol, "1m", since=end_timestamp, limit=1
        )
        return (price_end[0][1] >= price_initial[0][1], False)
    except Exception as e:
        print(f"Error getting trueval for {symbol} {e}")
        return (False, True)

def main(testing=False):
    config = TruevalConfig()
    t = TruevalAgent(config, get_true_val)
    t.run(testing)


if __name__ == "__main__":
    main()
