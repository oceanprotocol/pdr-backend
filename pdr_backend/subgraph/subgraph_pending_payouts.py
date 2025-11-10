import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta, timezone
from enforce_typing import enforce_types

from pdr_backend.subgraph.core_subgraph import query_subgraph
from pdr_backend.util.logutil import logging_has_stdout
from pdr_backend.util.time_types import UnixTimeS

logger = logging.getLogger("subgraph")


def _fetch_subgraph_payouts(
    subgraph_url: str,
    addr: str,
    slot_filter: str,
    chunk_size: int,
    include_paused: bool = False,
) -> List[Dict[str, Any]]:
    """
    slot_filter: string inside slot_{ ... } e.g.
        'status_in: ["Paying","Canceled"]'
        or 'status_in: ["Paying","Canceled","Pending"], slot_gte: %d, slot_lt: %d' % (a,b)
    include_paused: if True, include paused contracts in the query
    """
    results = []
    offset = 0
    while True:
        # Conditionally add the paused filter
        paused_filter = "" if include_paused else ", predictContract_: {paused: false}"

        query = """
        {
            predictPredictions(
            where: { user: "%s", payout: null, slot_: { %s%s } },
            first: %d,
            skip: %d
            ) {
            id
            timestamp
            slot {
                id
                slot
                predictContract { id }
            }
            }
        }
        """ % (
            addr,
            slot_filter,
            paused_filter,
            chunk_size,
            offset,
        )

        if logging_has_stdout():
            print(".", end="", flush=True)

        try:
            result = query_subgraph(subgraph_url, query)
            if "data" not in result or not result["data"]:
                logger.warning("No data in result")
                break
            page = result["data"].get("predictPredictions", [])
            if not page:
                break

            results.extend(page)
            offset += len(page)
            if len(page) < chunk_size:
                break
        except Exception as e:
            logger.warning("An error occured: %s", e)
            break

    return results


@enforce_types
def query_pending_payouts(
    subgraph_url: str, addr: str, query_old_slots=False, include_paused=False
) -> Dict[str, List[UnixTimeS]]:
    """
    Fetch pending payouts for a given address.
        Parameters:
    subgraph_url (str): The URL of the subgraph to query.
    addr (str): The address to fetch pending payouts for.
    query_old_slots (bool): Whether to query old slots (older than 3 days).
    include_paused (bool): Whether to include paused contracts in the query.
        Returns:
    Dict[str, List[UnixTimeS]]: A dictionary mapping contract addresses to lists of pending slot timestamps.
    """
    chunk_size = 1000
    pending_slots: Dict[str, List[UnixTimeS]] = {}
    addr = addr.lower()

    # payouts in "Paying", "Canceled" state
    query1_results: List[Dict[str, Any]] = []

    # payouts older than 3 days and pending
    query2_results: List[Dict[str, Any]] = []

    today_utc = datetime.now(timezone.utc).date()
    target_day = today_utc - timedelta(days=3)
    ts_end = datetime.combine(
        target_day, datetime.min.time(), tzinfo=timezone.utc
    ).timestamp()

    query1_results = _fetch_subgraph_payouts(
        subgraph_url=subgraph_url,
        addr=addr,
        slot_filter='status_in: ["Paying", "Canceled"]',
        chunk_size=chunk_size,
        include_paused=include_paused,
    )

    query2_results = []
    if query_old_slots:
        query2_results = _fetch_subgraph_payouts(
            subgraph_url=subgraph_url,
            addr=addr,
            slot_filter='status_in: ["Pending"], slot_lt: %d' % (ts_end),
            chunk_size=chunk_size,
            include_paused=include_paused,
        )

    merged = query1_results + query2_results
    for prediction in merged:
        contract_address = prediction["slot"]["predictContract"]["id"]
        timestamp = UnixTimeS(prediction["slot"]["slot"])
        pending_slots.setdefault(contract_address, []).append(timestamp)

    return pending_slots
