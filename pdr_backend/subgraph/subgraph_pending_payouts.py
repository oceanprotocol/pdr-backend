import logging
from typing import Dict, List

from enforce_typing import enforce_types

from pdr_backend.subgraph.core_subgraph import query_subgraph

logger = logging.getLogger(__name__)


@enforce_types
def query_pending_payouts(subgraph_url: str, addr: str) -> Dict[str, List[int]]:
    chunk_size = 1000
    offset = 0
    pending_slots: Dict[str, List[int]] = {}
    addr = addr.lower()

    while True:
        query = """
        {
                predictPredictions(
                    where: {user: "%s", payout: null, slot_: {status: "Paying"} }, first: %s, skip: %s
                ) {
                    id
                    timestamp
                    slot {
                        id
                        slot
                        predictContract {
                            id
                        }
                    }
                }
        }
        """ % (
            addr,
            chunk_size,
            offset,
        )
        offset += chunk_size
        # TODO
        print(".", end="", flush=True)
        try:
            result = query_subgraph(subgraph_url, query)
            if "data" not in result or not result["data"]:
                logger.warning("No data in result")
                break
            predict_predictions = result["data"].get("predictPredictions", [])
            if not predict_predictions:
                break
            for prediction in predict_predictions:
                contract_address = prediction["slot"]["predictContract"]["id"]
                timestamp = prediction["slot"]["slot"]
                pending_slots.setdefault(contract_address, []).append(timestamp)
        except Exception as e:
            logger.warning("An error occured: %s", e)
            break

    return pending_slots
