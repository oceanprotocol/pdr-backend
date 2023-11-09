from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional
from enforce_typing import enforce_types

from pdr_backend.util.subgraph import query_subgraph
from pdr_backend.util.networkutil import get_subgraph_url


@dataclass
class PredictSlot:
    id: str
    slot: str
    trueValues: List[Dict[str, Any]]
    roundSumStakesUp: float
    roundSumStakes: float


@enforce_types
def get_predict_slots_query(
    asset_ids: List[str], initial_slot: int, last_slot: int, first: int, skip: int
) -> str:
    """
    Constructs a GraphQL query string to fetch prediction slot data for
    specified assets within a slot range.

    Args:
        asset_ids: A list of asset identifiers to include in the query.
        initial_slot: The starting slot number for the query range.
        last_slot: The ending slot number for the query range.
        first: The number of records to fetch per query (pagination limit).
        skip: The number of records to skip (pagination offset).

    Returns:
        A string representing the GraphQL query.
    """
    asset_ids_str = str(asset_ids).replace("[", "[").replace("]", "]").replace("'", '"')

    return """
        query {
            predictSlots (
            first: %s
            skip: %s
            where: {
                slot_lte: %s
                slot_gte: %s
                predictContract_in: %s
            }
            ) {
            id
            slot
            trueValues {
                id
                trueValue
            }
            roundSumStakesUp
            roundSumStakes
            }
        }
    """ % (
        first,
        skip,
        initial_slot,
        last_slot,
        asset_ids_str,
    )


SECONDS_IN_A_DAY = 86400


@enforce_types
def get_slots(
    addresses: List[str],
    end_ts_param: int,
    start_ts_param: int,
    skip: int,
    slots: List[PredictSlot],
    network: str = "mainnet",
) -> List[PredictSlot]:
    """
    Retrieves slots information for given addresses and a specified time range from a subgraph.

    Args:
        addresses: A list of contract addresses to query.
        end_ts_param: The Unix timestamp representing the end of the time range.
        start_ts_param: The Unix timestamp representing the start of the time range.
        skip: The number of records to skip for pagination.
        slots: An existing list of slots to which new data will be appended.
        network: The blockchain network to query ('mainnet' or 'testnet').

    Returns:
        A list of PredictSlot TypedDicts with the queried slot information.
    """

    slots = slots or []

    records_per_page = 1000

    query = get_predict_slots_query(
        addresses,
        end_ts_param,
        start_ts_param,
        records_per_page,
        skip,
    )

    result = query_subgraph(
        get_subgraph_url(network),
        query,
        timeout=20.0,
    )

    new_slots = result["data"]["predictSlots"] or []

    # Convert the list of dicts to a list of PredictSlot objects
    # by passing the dict as keyword arguments
    # convert roundSumStakesUp and roundSumStakes to float
    new_slots = [
        PredictSlot(
            **{
                **slot,
                "roundSumStakesUp": float(slot["roundSumStakesUp"]),
                "roundSumStakes": float(slot["roundSumStakes"]),
            }
        )
        for slot in new_slots
    ]

    slots.extend(new_slots)
    if len(new_slots) == records_per_page:
        return get_slots(
            addresses,
            end_ts_param,
            start_ts_param,
            skip + records_per_page,
            slots,
            network,
        )
    return slots


@enforce_types
def fetch_slots_for_all_assets(
    asset_ids: List[str],
    start_ts_param: int,
    end_ts_param: int,
    network: str = "mainnet",
) -> Dict[str, List[PredictSlot]]:
    """
    Fetches slots for all provided asset IDs within a given time range and organizes them by asset.

    Args:
        asset_ids: A list of asset identifiers for which slots will be fetched.
        start_ts_param: The Unix timestamp marking the beginning of the desired time range.
        end_ts_param: The Unix timestamp marking the end of the desired time range.
        network: The blockchain network to query ('mainnet' or 'testnet').

    Returns:
        A dictionary mapping asset IDs to lists of PredictSlot dataclass
        containing slot information.
    """

    all_slots = get_slots(asset_ids, end_ts_param, start_ts_param, 0, [], network)

    slots_by_asset: Dict[str, List[PredictSlot]] = {}
    for slot in all_slots:
        slot_id = slot.id
        # split the id to get the asset id
        asset_id = slot_id.split("-")[0]
        if asset_id not in slots_by_asset:
            slots_by_asset[asset_id] = []

        slots_by_asset[asset_id].append(slot)

    return slots_by_asset


@enforce_types
def calculate_prediction_prediction_result(
    round_sum_stakes_up: float, round_sum_stakes: float
) -> Dict[str, bool]:
    """
    Calculates the prediction result based on the sum of stakes.

    Args:
        round_sum_stakes_up: The summed stakes for the 'up' prediction.
        round_sum_stakes: The summed stakes for the 'down' prediction.

    Returns:
        A dictionary with a boolean indicating the predicted direction.
    """

    return {"direction": round_sum_stakes_up > round_sum_stakes}


@enforce_types
def process_single_slot(
    slot: PredictSlot, end_of_previous_day_timestamp: int
) -> Optional[Tuple[float, float, int, int]]:
    """
    Processes a single slot and calculates the staked amounts for yesterday and today,
    as well as the count of correct predictions.

    Args:
        slot: A PredictSlot TypedDict containing information about a single prediction slot.
        end_of_previous_day_timestamp: The Unix timestamp marking the end of the previous day.

    Returns:
        A tuple containing staked amounts for yesterday, today, and the counts of correct
        predictions and slots evaluated, or None if no stakes were made today.
    """

    staked_yesterday = staked_today = 0.0
    correct_predictions_count = slots_evaluated = 0
    # split the id to get the slot timestamp
    timestamp = int(slot.id.split("-")[1])  # Using dot notation for attribute access

    if timestamp < end_of_previous_day_timestamp:
        staked_yesterday += float(slot.roundSumStakes)
    else:
        staked_today += float(slot.roundSumStakes)
        if float(slot.roundSumStakes) == 0:
            return None

        prediction_result = calculate_prediction_prediction_result(
            slot.roundSumStakesUp, slot.roundSumStakes
        )
        true_values: List[Dict[str, Any]] = slot.trueValues or []
        true_value = true_values[0]["trueValue"] if true_values else None
        if true_values and prediction_result["direction"] == (1 if true_value else 0):
            correct_predictions_count += 1
        slots_evaluated += 1

    return staked_yesterday, staked_today, correct_predictions_count, slots_evaluated


@enforce_types
def aggregate_statistics(
    slots: List[PredictSlot], end_of_previous_day_timestamp: int
) -> Tuple[float, float, int, int]:
    """
    Aggregates statistics across all provided slots for an asset.

    Args:
        slots: A list of PredictSlot TypedDicts containing information
            about multiple prediction slots.
        end_of_previous_day_timestamp: The Unix timestamp marking the end of the previous day.

    Returns:
        A tuple containing the total staked amounts for yesterday, today,
        and the total counts of correct predictions and slots evaluated.
    """

    total_staked_yesterday = (
        total_staked_today
    ) = total_correct_predictions = total_slots_evaluated = 0
    for slot in slots:
        slot_results = process_single_slot(slot, end_of_previous_day_timestamp)
        if slot_results:
            (
                staked_yesterday,
                staked_today,
                correct_predictions_count,
                slots_evaluated,
            ) = slot_results
            total_staked_yesterday += staked_yesterday
            total_staked_today += staked_today
            total_correct_predictions += correct_predictions_count
            total_slots_evaluated += slots_evaluated
    return (
        total_staked_yesterday,
        total_staked_today,
        total_correct_predictions,
        total_slots_evaluated,
    )


@enforce_types
def calculate_statistics_for_all_assets(
    asset_ids: List[str],
    start_ts_param: int,
    end_ts_param: int,
    network: str = "mainnet",
) -> Dict[str, Dict[str, Any]]:
    """
    Calculates statistics for all provided assets based on
    slot data within a specified time range.

    Args:
        asset_ids: A list of asset identifiers for which statistics will be calculated.
        start_ts_param: The Unix timestamp for the start of the time range.
        end_ts_param: The Unix timestamp for the end of the time range.
        network: The blockchain network to query ('mainnet' or 'testnet').

    Returns:
        A dictionary mapping asset IDs to another dictionary with
        calculated statistics such as average accuracy and total staked amounts.
    """
    slots_by_asset = fetch_slots_for_all_assets(
        asset_ids, start_ts_param, end_ts_param, network
    )

    overall_stats = {}
    for asset_id, slots in slots_by_asset.items():
        (
            staked_yesterday,
            staked_today,
            correct_predictions_count,
            slots_evaluated,
        ) = aggregate_statistics(slots, end_ts_param - SECONDS_IN_A_DAY)
        average_accuracy = (
            0
            if correct_predictions_count == 0
            else (correct_predictions_count / slots_evaluated) * 100
        )
        overall_stats[asset_id] = {
            "average_accuracy": average_accuracy,
            "total_staked_yesterday": staked_yesterday,
            "total_staked_today": staked_today,
        }
    return overall_stats
