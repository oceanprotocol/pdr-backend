import logging

from enforce_typing import enforce_types

from pdr_backend.ppss.publisher_ss import PublisherSS
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.publisher.publish_asset import publish_asset

logger = logging.getLogger("publisher")
_CUT = 0.2
_RATE = 3 / (1 + _CUT + 0.001)  # token price
_S_PER_SUBSCRIPTION = 60 * 60 * 24


@enforce_types
def publish_assets(web3_pp: Web3PP, publisher_ss: PublisherSS):
    """
    Publish assets, with opinions on % cut, token price, subscription length,
      timeframe, and choices of feeds.
    Meant to be used from CLI.
    """
    logger.info("Publish on network = %s", web3_pp.network)
    if web3_pp.network == "development" or "barge" in web3_pp.network:
        trueval_submitter_addr = "0xe2DD09d719Da89e5a3D0F2549c7E24566e947260"
        fee_collector_addr = "0xe2DD09d719Da89e5a3D0F2549c7E24566e947260"
    elif "sapphire" in web3_pp.network:
        trueval_submitter_addr = web3_pp.get_address("PredictoorHelper")
        fee_collector_addr = publisher_ss.fee_collector_address
    else:
        raise ValueError(web3_pp.network)

    for feed in publisher_ss.feeds:
        publish_asset(
            # timeframe is already asserted in PublisherSS
            s_per_epoch=feed.timeframe.s,  # type: ignore[union-attr]
            s_per_subscription=_S_PER_SUBSCRIPTION,
            feed=feed,
            trueval_submitter_addr=trueval_submitter_addr,
            feeCollector_addr=fee_collector_addr,
            rate=_RATE,
            cut=_CUT,
            web3_pp=web3_pp,
        )
    logger.info("Done publishing.")
