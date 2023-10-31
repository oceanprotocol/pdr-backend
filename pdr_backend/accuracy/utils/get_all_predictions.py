from typing import List
from pdr_backend.util.subgraph import query_subgraph
from models.prediction import Prediction
from pdr_backend.util.subgraph import info_from_725
from pdr_backend.accuracy.utils.get_subgraph_url import get_subgraph_url

def get_all_predictions(start_ts: int, end_ts: int, contract_addresses: List[str], network: str):
    if network != "mainnet" and network != "testnet":
        raise Exception("Invalid network, pick mainnet or testnet")

    chunk_size = 1000
    offset = 0
    predictions: List[Prediction] = []

    contract_addresses = [addr.lower() for addr in contract_addresses]

    while True:
        query = """
            {
            predictPredictions(skip: %s, first: %s, where: {slot_: {predictContract_in: %s, slot_gt: %s, slot_lt: %s}}) {
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
            str(contract_addresses).replace("'", '"'),
            start_ts,
            end_ts,
        )

        print("Querying subgraph...", query)

        result = query_subgraph(
            get_subgraph_url(network),
            query,
            timeout=20.0,
        )

        # print("subgraph", mainnet_subgraph)
        # print("result", result)
        print("predictionslength", len(predictions))

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
                print("prediction payout is None")
                continue

            trueval = prediction["payout"]["trueValue"]
            payout = float(prediction["payout"]["payout"])

            if trueval is None:
                print("trueval is None")
                continue

            predictedValue = prediction["payout"]["predictedValue"]
            stake = float(prediction["stake"])
            predictoor_user = prediction["user"]["id"]
            if stake < 0.01:
                print("stake is None")
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
