from enforce_typing import enforce_types

from pdr_backend.exchange.ccxtutil import CCXTExchangeMixin
from pdr_backend.ppss.base_ss import SingleFeedMixin


class SingleFeedMixinTest(SingleFeedMixin):
    FEED_KEY = "feed"


class CCXTExchangeMixinTest(SingleFeedMixinTest, CCXTExchangeMixin):
    pass


@enforce_types
def test_ccxt_mixin():
    ccxt_mixin = CCXTExchangeMixinTest(
        {"feed": "binance ETH/USDT 5m", "exchange_only": {"key1": "val1"}}
    )
    assert len(ccxt_mixin.exchange_params.keys()) == 3
    assert "apiKey" in ccxt_mixin.exchange_params
    assert "secret" in ccxt_mixin.exchange_params
    assert ccxt_mixin.exchange_params["key1"] == "val1"
