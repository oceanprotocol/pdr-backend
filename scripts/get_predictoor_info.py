import csv
from typing import List
from pdr_backend.util.subgraph import query_subgraph


class Prediction:
    def __init__(self, pair, timeframe, prediction, stake, trueval, timestamp, source) -> None:
        self.pair = pair
        self.timeframe = timeframe
        self.prediction = prediction
        self.stake = stake
        self.trueval = trueval
        self.timestamp = timestamp
        self.source = source


def get_all_predictions(start_ts: int, end_ts: int, predictoor_addr: str, network: str):

    if network != "mainnet" or network != "testnet":
        raise Exception("Invalid network, pick mainnet or testnet")

    chunk_size = 1000
    offset = 0
    predictions: List[Prediction] = []

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
        mainnet_subgraph = "https://v4.subgraph.sapphire-mainnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph"
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
            predictoor_key = [
                key
                for key, value in addresses.items()
                if value.lower() == prediction["user"]["id"]
            ][0]
            info725 = prediction["slot"]["predictContract"]["token"]["nft"]["nftData"]
            pair_name = info["pair"]
            timeframe = info["timeframe"]
            source = info["source"]
            timestamp = prediction["slot"]["slot"]

            if prediction["payout"] is None:
                continue

            trueval = prediction["payout"]["trueValue"]

            if trueval is None:
                continue

            predictedValue = prediction["payout"]["predictedValue"]
            stake = float(prediction["stake"])

            if stake < 0.01:
                continue

            prediction_obj = Prediction(
                pair_name, timeframe, predictedValue, stake, trueval, timestamp, source
            )
            predictions.append(prediction_obj)

    return predictions


def write_csv(all_predictions):
    data = {}
    for prediction in all_predictions:
        key = prediction.pair + prediction.timeframe + prediction.source
        if key not in data:
            data[key] = []
        data[key].append(prediction)
    for key, prediction in data.items():
        prediction.sort(key=lambda x: x.timestamp)
        filename = key + ".csv"
        with open(filename, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Predicted Value", "True Value", "Timestamp", "Stake"])
            for prediction in prediction:
                writer.writerow(
                    [
                        prediction.prediction,
                        prediction.trueval,
                        prediction.timestamp,
                        prediction.stake,
                    ]
                )
        print(f"CSV file '{filename}' created successfully.")


if __name__ == "__main__":
    PREDICTOOR_ADDR = ""
    START_TS = ""
    END_TS = ""
    NETWORK = "mainnet"
    _predictions = get_all_predictions()
    write_csv(_predictions)
