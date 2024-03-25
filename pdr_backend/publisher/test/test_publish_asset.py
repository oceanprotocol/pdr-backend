from enforce_typing import enforce_types
from pytest import approx

from pdr_backend.contract.feed_contract import FeedContract
from pdr_backend.publisher.publish_asset import publish_asset
from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.util.currency_types import Eth


@enforce_types
def test_publish_asset(web3_pp, web3_config):
    feed = ArgFeed("kraken", None, "ETH/USDT", "5m")
    seconds_per_epoch = 300
    seconds_per_subscription = 60 * 60 * 24
    nft_data, _, _, _, logs_erc = publish_asset(
        s_per_epoch=seconds_per_epoch,
        s_per_subscription=seconds_per_subscription,
        feed=feed,
        trueval_submitter_addr=web3_config.owner,
        feeCollector_addr=web3_config.owner,
        rate=Eth(3),
        cut=Eth(0.2),
        web3_pp=web3_pp,
    )

    base = feed.pair.base_str
    quote = feed.pair.quote_str
    source = str(feed.exchange)
    timeframe = str(feed.timeframe)

    nft_name = base + "-" + quote + "-" + source + "-" + timeframe
    nft_symbol = base + "/" + quote
    assert nft_data == (nft_name, nft_symbol, 1, "", True, web3_config.owner)

    dt_addr = logs_erc["newTokenAddress"]
    assert web3_config.w3.is_address(dt_addr)

    contract = FeedContract(web3_pp, dt_addr)

    assert contract.get_secondsPerEpoch() == seconds_per_epoch
    assert (
        contract.contract_instance.functions.secondsPerSubscription().call()
        == seconds_per_subscription
    )
    assert contract.get_price().amt_wei / 1e18 == approx(3 * (1.201))

    assert contract.get_stake_token() == web3_pp.OCEAN_address

    assert contract.get_trueValSubmitTimeout() == 3 * 24 * 60 * 60
