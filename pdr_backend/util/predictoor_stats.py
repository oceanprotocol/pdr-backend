from typing import List, Dict, Tuple, TypedDict, Set
from enforce_typing import enforce_types
from pdr_backend.models.prediction import Prediction


class PairTimeframeStat(TypedDict):
    pair: str
    timeframe: str
    accuracy: float
    stake: float
    payout: float
    number_of_predictions: int


class PredictoorStat(TypedDict):
    predictoor_address: str
    accuracy: float
    stake: float
    payout: float
    number_of_predictions: int
    details: Set[Tuple[str, str, str]]


@enforce_types
def aggregate_prediction_statistics(
    all_predictions: List[Prediction],
) -> Tuple[Dict[str, Dict], int]:
    """
    Aggregates statistics from a list of prediction objects. It organizes statistics
    by currency pair and timeframe and predictor address. For each category, it
    tallies the total number of predictions, the number of correct predictions,
    and the total stakes and payouts. It also returns the total number of correct
    predictions across all categories.

    Args:
        all_predictions (List[Prediction]): A list of Prediction objects to aggregate.

    Returns:
        Tuple[Dict[str, Dict], int]: A tuple containing a dictionary of aggregated
        statistics and the total number of correct predictions.
    """
    stats: Dict[str, Dict] = {"pair_timeframe": {}, "predictor": {}}
    correct_predictions = 0

    for prediction in all_predictions:
        pair_timeframe_key = (prediction.pair, prediction.timeframe)
        predictor_key = prediction.user
        source = prediction.source

        is_correct = prediction.prediction == prediction.trueval

        if pair_timeframe_key not in stats["pair_timeframe"]:
            stats["pair_timeframe"][pair_timeframe_key] = {
                "correct": 0,
                "total": 0,
                "stake": 0,
                "payout": 0,
            }

        if predictor_key not in stats["predictor"]:
            stats["predictor"][predictor_key] = {
                "correct": 0,
                "total": 0,
                "stake": 0,
                "payout": 0,
                "details": set(),
            }

        if is_correct:
            correct_predictions += 1
            stats["pair_timeframe"][pair_timeframe_key]["correct"] += 1
            stats["predictor"][predictor_key]["correct"] += 1

        stats["pair_timeframe"][pair_timeframe_key]["total"] += 1
        stats["pair_timeframe"][pair_timeframe_key]["stake"] += prediction.stake
        stats["pair_timeframe"][pair_timeframe_key]["payout"] += prediction.payout

        stats["predictor"][predictor_key]["total"] += 1
        stats["predictor"][predictor_key]["stake"] += prediction.stake
        stats["predictor"][predictor_key]["payout"] += prediction.payout
        stats["predictor"][predictor_key]["details"].add(
            (prediction.pair, prediction.timeframe, source)
        )

    return stats, correct_predictions


@enforce_types
def get_endpoint_statistics(
    all_predictions: List[Prediction],
) -> Tuple[float, List[PairTimeframeStat], List[PredictoorStat]]:
    """
    Calculates the overall accuracy of predictions, and aggregates detailed prediction
    statistics by currency pair and timeframe with predictoor.

    The function first determines the overall accuracy of all given predictions.
    It then organizes individual prediction statistics into two separate lists:
    one for currency pair and timeframe statistics, and another for predictor statistics.

    Args:
        all_predictions (List[Prediction]): A list of Prediction objects to be analyzed.

    Returns:
        Tuple[float, List[Dict[str, Any]], List[Dict[str, Any]]]: A tuple containing the
        overall accuracy as a float, a list of dictionaries with statistics for each
        currency pair and timeframe, and a list of dictionaries with statistics for each
        predictor.
    """
    total_predictions = len(all_predictions)
    stats, correct_predictions = aggregate_prediction_statistics(all_predictions)

    overall_accuracy = (
        correct_predictions / total_predictions * 100 if total_predictions else 0
    )

    pair_timeframe_stats: List[PairTimeframeStat] = []
    for key, stat_pair_timeframe_item in stats["pair_timeframe"].items():
        pair, timeframe = key
        accuracy = (
            stat_pair_timeframe_item["correct"]
            / stat_pair_timeframe_item["total"]
            * 100
            if stat_pair_timeframe_item["total"]
            else 0
        )
        pair_timeframe_stat: PairTimeframeStat = {
            "pair": pair,
            "timeframe": timeframe,
            "accuracy": accuracy,
            "stake": stat_pair_timeframe_item["stake"],
            "payout": stat_pair_timeframe_item["payout"],
            "number_of_predictions": stat_pair_timeframe_item["total"],
        }
        pair_timeframe_stats.append(pair_timeframe_stat)

    predictoor_stats: List[PredictoorStat] = []
    for predictoor_addr, stat_predictoor_item in stats["predictor"].items():
        accuracy = (
            stat_predictoor_item["correct"] / stat_predictoor_item["total"] * 100
            if stat_predictoor_item["total"]
            else 0
        )
        predictoor_stat: PredictoorStat = {
            "predictoor_address": predictoor_addr,
            "accuracy": accuracy,
            "stake": stat_predictoor_item["stake"],
            "payout": stat_predictoor_item["payout"],
            "number_of_predictions": stat_predictoor_item["total"],
            "details": set(stat_predictoor_item["details"]),
        }
        predictoor_stats.append(predictoor_stat)

    return overall_accuracy, pair_timeframe_stats, predictoor_stats


@enforce_types
def get_cli_statistics(all_predictions: List[Prediction]) -> None:
    total_predictions = len(all_predictions)

    stats, correct_predictions = aggregate_prediction_statistics(all_predictions)

    if total_predictions == 0:
        print("No predictions found.")
        return

    if correct_predictions == 0:
        print("No correct predictions found.")
        return

    print(f"Overall Accuracy: {correct_predictions/total_predictions*100:.2f}%")

    for key, stat_pair_timeframe_item in stats["pair_timeframe"].items():
        pair, timeframe = key
        accuracy = (
            stat_pair_timeframe_item["correct"]
            / stat_pair_timeframe_item["total"]
            * 100
        )
        print(f"Accuracy for Pair: {pair}, Timeframe: {timeframe}: {accuracy:.2f}%")
        print(f"Total stake: {stat_pair_timeframe_item['stake']}")
        print(f"Total payout: {stat_pair_timeframe_item['payout']}")
        print(f"Number of predictions: {stat_pair_timeframe_item['total']}\n")

    for predictoor_addr, stat_predictoor_item in stats["predictor"].items():
        accuracy = stat_predictoor_item["correct"] / stat_predictoor_item["total"] * 100
        print(f"Accuracy for Predictoor Address: {predictoor_addr}: {accuracy:.2f}%")
        print(f"Stake: {stat_predictoor_item['stake']}")
        print(f"Payout: {stat_predictoor_item['payout']}")
        print(f"Number of predictions: {stat_predictoor_item['total']}")
        print("Details of Predictions:")
        for detail in stat_predictoor_item["details"]:
            print(f"Pair: {detail[0]}, Timeframe: {detail[1]}, Source: {detail[2]}")
        print("\n")
