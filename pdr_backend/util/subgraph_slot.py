from typing import List, Dict, Any, TypedDict

from pdr_backend.util.subgraph import query_subgraph
from pdr_backend.util.subgraph_predictions import get_subgraph_url


class Slot(TypedDict):
    id: str
    slot: str
    trueValues: List[Dict[str, Any]]
    roundSumStakesUp: float
    roundSumStakes: float


def get_predict_slots_query(
    asset_ids: List[str], initial_slot: int, last_slot: int, first: int, skip: int
) -> str:
    # Convert list of asset_ids to a GraphQL array format
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


def get_slots(
    addresses: List[str],
    end_ts_param: int,
    start_ts_param: int,
    skip: int,
    slots: List[Slot],
    network: str = "mainnet",
) -> List[Slot]:
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


def fetch_slots_for_all_assets(
    asset_ids: List[str],
    start_ts_param: int,
    end_ts_param: int,
    network: str = "mainnet",
) -> Dict[str, List[Slot]]:
    all_slots = get_slots(asset_ids, end_ts_param, start_ts_param, 0, [], network)

    slots_by_asset: Dict[str, List[Slot]] = {}
    for slot in all_slots:
        slot_id = slot["id"]
        # split the id to get the asset id
        asset_id = slot_id.split("-")[0]
        if asset_id not in slots_by_asset:
            slots_by_asset[asset_id] = []
        slots_by_asset[asset_id].append(slot)

    return slots_by_asset


def calculate_prediction_prediction_result(
    round_sum_stakes_up: float, round_sum_stakes: float
):
    return {"direction": round_sum_stakes_up > round_sum_stakes}


# Function to process individual slot data
def process_single_slot(slot: Slot, end_of_previous_day_timestamp: int):
    staked_yesterday = staked_today = 0.0
    correct_predictions_count = slots_evaluated = 0
    # split the id to get the slot timestamp
    timestamp = int(slot["id"].split("-")[1])

    if timestamp < end_of_previous_day_timestamp:
        staked_yesterday += float(slot["roundSumStakes"])
    else:
        staked_today += float(slot["roundSumStakes"])
        if float(slot["roundSumStakes"]) == 0:
            return None

        prediction_result = calculate_prediction_prediction_result(
            slot["roundSumStakesUp"], slot["roundSumStakes"]
        )
        true_values: List[Dict[str, Any]] = slot.get("trueValues", [])
        true_value = true_values[0]["trueValue"] if true_values else None
        if true_values and prediction_result["direction"] == (1 if true_value else 0):
            correct_predictions_count += 1
        slots_evaluated += 1

    return staked_yesterday, staked_today, correct_predictions_count, slots_evaluated


# Function to aggregate statistics across all slots for an asset
def aggregate_statistics(slots: List[Slot], end_of_previous_day_timestamp: int):
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


# Function to calculate stats for all assets
def calculate_statistics_for_all_assets(
    asset_ids: List[str],
    start_ts_param: int,
    end_ts_param: int,
    network: str = "mainnet",
):
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
