from typing import List, Dict, Tuple, Union
from models.prediction import Prediction

PredictionDetail = Tuple[str, str, str]
PredictoorStats = Dict[str, Union[str, float, int, List[PredictionDetail]]]
PairTimeframeStats = Dict[str, Union[str, float, int]]
StatisticsResult = Dict[str, Union[float, List[PredictoorStats], List[PairTimeframeStats]]]

def extract_statistics(all_predictions: List[Prediction]) -> StatisticsResult:
    # This is similar to the get_statistics function but returns the results instead of printing them.
    total_predictions = len(all_predictions)
    correct_predictions = 0
    stats = {"pair_timeframe": {}, "predictoor": {}}

    for prediction in all_predictions:
        pair_timeframe_key = (prediction.pair, prediction.timeframe)
        predictoor_key = prediction.user
        source = prediction.source

        is_correct = prediction.prediction == prediction.trueval

        if pair_timeframe_key not in stats["pair_timeframe"]:
            stats["pair_timeframe"][pair_timeframe_key] = {
                "correct": 0,
                "total": 0,
                "stake": 0,
                "payout": 0,
            }

        if predictoor_key not in stats["predictoor"]:
            stats["predictoor"][predictoor_key] = {
                "correct": 0,
                "total": 0,
                "stake": 0,
                "payout": 0,
                "details": set(),
            }

        if is_correct:
            correct_predictions += 1
            stats["pair_timeframe"][pair_timeframe_key]["correct"] += 1
            stats["predictoor"][predictoor_key]["correct"] += 1

        stats["pair_timeframe"][pair_timeframe_key]["total"] += 1
        stats["pair_timeframe"][pair_timeframe_key]["stake"] += prediction.stake
        stats["pair_timeframe"][pair_timeframe_key]["payout"] += prediction.payout

        stats["predictoor"][predictoor_key]["total"] += 1
        stats["predictoor"][predictoor_key]["stake"] += prediction.stake
        stats["predictoor"][predictoor_key]["payout"] += prediction.payout
        stats["predictoor"][predictoor_key]["details"].add(
            (prediction.pair, prediction.timeframe, source)
        )

    overall_accuracy = correct_predictions / total_predictions * 100 if total_predictions else 0

    results = {
        "overall_accuracy": overall_accuracy,
        "pair_timeframe_stats": [],
        "predictoor_stats": []
    }

    for key, data in stats["pair_timeframe"].items():
        pair, timeframe = key
        accuracy = data["correct"] / data["total"] * 100 if data["total"] else 0
        results["pair_timeframe_stats"].append({
            "pair": pair,
            "timeframe": timeframe,
            "accuracy": accuracy,
            "stake": data["stake"],
            "payout": data["payout"],
            "number_of_predictions": data["total"]
        })

    for predictoor, data in stats["predictoor"].items():
        accuracy = data["correct"] / data["total"] * 100 if data["total"] else 0
        results["predictoor_stats"].append({
            "predictoor_address": predictoor,
            "accuracy": accuracy,
            "stake": data["stake"],
            "payout": data["payout"],
            "number_of_predictions": data["total"],
            "details": list(data["details"])
        })

    return results
