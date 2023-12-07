from enforce_typing import enforce_types

from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.ppss.publisher_ss import PublisherSS
from pdr_backend.publisher.publish_asset import publish_asset
from pdr_backend.util.contract import get_address
from pdr_backend.util.feedstr import unpack_feeds_strs
from pdr_backend.util.pairstr import unpack_pair_str
from pdr_backend.util.timeframestr import Timeframe


_CUT = 0.2
_RATE = 3 / (1 + _CUT + 0.001)  # token price
_S_PER_SUBSCRIPTION = 60 * 60 * 24

_TIMEFRAME_STRS = {
    "development": ["5m"],
    "sapphire-testnet": ["5m", "1h"],
    "sapphire-mainnet": ["5m", "1h"],
}

_SOME = "BTC/USDT ETH/USDT XRP/USDT"
_ALL = "BTC/USDT ETH/USDT BNB/USDT XRP/USDT ADA/USDT DOGE/USDT SOL/USDT LTC/USDT TRX/USDT DOT/USDT"
_FEEDS_STRS = {
    "development": [f"binance c {_SOME}"],
    "sapphire-testnet": [f"binance c {_ALL}"],
    "sapphire-mainnet": [f"binance c {_ALL}"],
}


@enforce_types
def publish_assets(web3_pp: Web3PP, publisher_ss: PublisherSS):
    """
    Publish assets, with opinions on % cut, token price, subscription length,
      timeframe, and choices of feeds.
    Meant to be used from CLI.
    """
    print(f"Publish on network = {web3_pp.network}")
    if web3_pp.network == "development":
        trueval_submitter_addr = "0xe2DD09d719Da89e5a3D0F2549c7E24566e947260"
        fee_collector_addr = "0xe2DD09d719Da89e5a3D0F2549c7E24566e947260"
    elif "sapphire" in web3_pp.network:
        trueval_submitter_addr = get_address(web3_pp, "PredictoorHelper")
        fee_collector_addr = publisher_ss.fee_collector_address
    else:
        raise ValueError(web3_pp.network)

    for timeframe_str in _TIMEFRAME_STRS[web3_pp.network]:
        feed_tups = unpack_feeds_strs(_FEEDS_STRS[web3_pp.network])
        for exchange_str, _, pair_str in feed_tups:
            base_str, quote_str = unpack_pair_str(pair_str)
            publish_asset(
                s_per_epoch=Timeframe(timeframe_str).s,
                s_per_subscription=_S_PER_SUBSCRIPTION,
                base=base_str,
                quote=quote_str,
                source=exchange_str,
                timeframe=timeframe_str,
                trueval_submitter_addr=trueval_submitter_addr,
                feeCollector_addr=fee_collector_addr,
                rate=_RATE,
                cut=_CUT,
                web3_pp=web3_pp,
            )
    print("Done publishing.")
