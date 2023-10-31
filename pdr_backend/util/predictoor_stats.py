from typing import List, Dict, Tuple, Union
from pdr_backend.models.prediction import Prediction

PredictionDetail = Tuple[str, str, str]
PredictoorStats = Dict[str, Union[str, float, int, List[PredictionDetail]]]
PairTimeframeStats = Dict[str, Union[str, float, int]]
StatisticsResult = Dict[str, Union[float, List[PredictoorStats], List[PairTimeframeStats]]]


def get_pure_stats(all_predictions: List[Prediction]):
    stats = {"pair_timeframe": {}, "predictoor": {}}
    correct_predictions = 0

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

    return stats, correct_predictions


def get_endpoint_statistics(all_predictions: List[Prediction]) -> StatisticsResult:
    # This is similar to the get_statistics function but returns the results instead of printing them.
    total_predictions = len(all_predictions)
    stats, correct_predictions = get_pure_stats(all_predictions)

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


def get_cli_statistics(all_predictions):
    total_predictions = len(all_predictions)
    
    stats, correct_predictions = get_pure_stats(all_predictions)
    print(f"Overall Accuracy: {correct_predictions/total_predictions*100:.2f}%")

    for key, data in stats["pair_timeframe"].items():
        pair, timeframe = key
        accuracy = data["correct"] / data["total"] * 100
        print(f"Accuracy for Pair: {pair}, Timeframe: {timeframe}: {accuracy:.2f}%")
        print(f"Total stake: {data['stake']}")
        print(f"Total payout: {data['payout']}")
        print(f"Number of predictions: {data['total']}\n")

    for predictoor, data in stats["predictoor"].items():
        accuracy = data["correct"] / data["total"] * 100
        print(f"Accuracy for Predictoor Address: {predictoor}: {accuracy:.2f}%")
        print(f"Stake: {data['stake']}")
        print(f"Payout: {data['payout']}")
        print(f"Number of predictions: {data['total']}")
        print("Details of Predictions:")
        for detail in data["details"]:
            print(f"Pair: {detail[0]}, Timeframe: {detail[1]}, Source: {detail[2]}")
        print("\n")
