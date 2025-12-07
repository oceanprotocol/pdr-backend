import logging
from typing import List

from enforce_typing import enforce_types

from pdr_backend.contract.feed_contract import FeedContract
from pdr_backend.ppss.web3_pp import Web3PP

logger = logging.getLogger("pause_predictions")


@enforce_types
def pause_predictions(web3_pp: Web3PP, contract_addresses: List[str]):
    """
    Pause predictions for a list of feed contracts.

    @arguments
      web3_pp: Web3PP instance with network configuration
      contract_addresses: List of contract addresses to pause
    """
    logger.info("Pausing predictions on network = %s", web3_pp.network)
    logger.info("Number of contracts to pause: %d", len(contract_addresses))

    successful = []
    failed = []

    for address in contract_addresses:
        logger.info("Pausing predictions for contract: %s", address)
        try:
            feed_contract = FeedContract(web3_pp, address)
            tx = feed_contract.pause_predictions(wait_for_receipt=True)

            if tx is not None:
                logger.info("Successfully paused predictions for %s", address)
                successful.append(address)
            else:
                logger.error("Failed to pause predictions for %s", address)
                failed.append(address)
        except Exception as e:
            logger.error("Error pausing predictions for %s: %s", address, e)
            failed.append(address)

    logger.info("Done pausing predictions.")
    logger.info("Successfully paused: %d", len(successful))
    logger.info("Failed to pause: %d", len(failed))

    if failed:
        logger.warning("Failed contracts: %s", failed)
