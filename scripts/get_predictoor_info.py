import csv
import time
from datetime import datetime
from typing import List
from pdr_backend.util.subgraph import info_from_725, query_subgraph


class Prediction:
    def __init__(
        self,
        pair,
        timeframe,
        prediction,
        stake,
        trueval,
        timestamp,
        source,
        payout,
        user,
    ) -> None:
        self.pair = pair
        self.timeframe = timeframe
        self.prediction = prediction
        self.stake = stake
        self.trueval = trueval
        self.timestamp = timestamp
        self.source = source
        self.payout = payout
        self.user = user


def get_all_predictions(start_ts: int, end_ts: int, predictoor_addr: str, network: str):
    if network != "mainnet" and network != "testnet":
        raise Exception("Invalid network, pick mainnet or testnet")

    chunk_size = 1000
    offset = 0
    predictions: List[Prediction] = []

    if "," in predictoor_addr:
        address_filter = predictoor_addr.lower().split(",")
    else:
        address_filter = [predictoor_addr.lower()]

    while True:
        query = """
            {
            predictPredictions(skip: %s, first: %s, where: {user_: {id_in: %s}, slot_: {slot_gt: %s, slot_lt: %s}}) {
                id
                user {
                    id
                }
                stake
                payout {
                    payout
                    trueValue
                    predictedValue
                }
                slot {
                    slot
                    predictContract {
                        id
                        token {
                            id
                            name
                            nft{
                                nftData {
                                key
                                value
                                }
                            }
                        }
                    }
                }
            }
            }
        """ % (
            offset,
            chunk_size,
            str(address_filter).replace("'", '"'),
            end_ts,
            start_ts,
        )

        # pylint: disable=line-too-long
        mainnet_subgraph = f"https://v4.subgraph.sapphire-{network}.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph"
        result = query_subgraph(
            mainnet_subgraph,
            query,
            timeout=10.0,
        )

        print(".")

        offset += 1000

        if not "data" in result:
            break

        data = result["data"]["predictPredictions"]
        if len(data) == 0:
            break
        for prediction in data:
            info725 = prediction["slot"]["predictContract"]["token"]["nft"]["nftData"]
            info = info_from_725(info725)
            pair_name = info["pair"]
            timeframe = info["timeframe"]
            source = info["source"]
            timestamp = prediction["slot"]["slot"]

            if prediction["payout"] is None:
                continue

            trueval = prediction["payout"]["trueValue"]
            payout = float(prediction["payout"]["payout"])

            if trueval is None:
                continue

            predictedValue = prediction["payout"]["predictedValue"]
            stake = float(prediction["stake"])
            predictoor_user = prediction["user"]["id"]
            if stake < 0.01:
                continue

            prediction_obj = Prediction(
                pair_name,
                timeframe,
                predictedValue,
                stake,
                trueval,
                timestamp,
                source,
                payout,
                predictoor_user,
            )
            predictions.append(prediction_obj)

    return predictions


def write_csv(all_predictions):
    data = {}
    for prediction in all_predictions:
        key = (
            prediction.pair.replace("/", "-") + prediction.timeframe + prediction.source
        )
        if key not in data:
            data[key] = []
        data[key].append(prediction)
    for key, prediction in data.items():
        prediction.sort(key=lambda x: x.timestamp)
        filename = key + ".csv"
        with open(filename, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(
                ["Predicted Value", "True Value", "Timestamp", "Stake", "Payout"]
            )
            for prediction in prediction:
                writer.writerow(
                    [
                        prediction.prediction,
                        prediction.trueval,
                        prediction.timestamp,
                        prediction.stake,
                        prediction.payout,
                    ]
                )
        print(f"CSV file '{filename}' created successfully.")


def date_to_unix(date_string):
    dt = datetime.strptime(date_string, "%Y-%m-%d")
    return int(time.mktime(dt.timetuple()))


def get_statistics(all_predictions):
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

    print(f"Overall Accuracy: {correct_predictions/total_predictions*100:.2f}%")

    for key, data in stats["pair_timeframe"].items():
        pair, timeframe = key
        accuracy = data["correct"] / data["total"] * 100
        print(f"Accuracy for Pair: {pair}, Timeframe: {timeframe}: {accuracy:.2f}%")
        print(f"Total stake: {data['stake']}")
        print(f"Total payout: {data['payout']}\n")

    for predictoor, data in stats["predictoor"].items():
        accuracy = data["correct"] / data["total"] * 100
        print(f"Accuracy for Predictoor Address: {predictoor}: {accuracy:.2f}%")
        print(f"Stake: {data['stake']}")
        print(f"Payout: {data['payout']}")
        print("Details of Predictions:")
        for detail in data["details"]:
            print(f"Pair: {detail[0]}, Timeframe: {detail[1]}, Source: {detail[2]}")
        print("\n")


if __name__ == "__main__":
    PREDICTOOR_ADDR = ""
    START_TS = "2023-10-20"
    END_TS = "2023-10-10"
    NETWORK = "mainnet"

    start_ts = date_to_unix(START_TS)
    end_ts = date_to_unix(END_TS)

    _predictions = get_all_predictions(start_ts, end_ts, PREDICTOOR_ADDR, NETWORK)
    write_csv(_predictions)

    get_statistics(_predictions)
