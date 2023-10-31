from typing import List
import json
from enum import Enum

from pdr_backend.util.subgraph import query_subgraph, info_from_725
from pdr_backend.models.prediction import Prediction


class FilterMode(Enum):
    CONTRACT = 1
    PREDICTOOR = 2


def get_subgraph_url(network: str) -> str:
    """
    Returns the subgraph URL for the given network.

    Args:
        network (str): The network name ("mainnet" or "testnet").

    Returns:
        str: The subgraph URL for the specified network.
    """
    if network not in ["mainnet", "testnet"]:
        raise ValueError(
            "Invalid network. Acceptable values are 'mainnet' or 'testnet'."
        )

    # pylint: disable=line-too-long
    return f"https://v4.subgraph.sapphire-{network}.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph"


def get_all_predictions(
    start_ts: int,
    end_ts: int,
    filters: List[str],
    network: str,
    filter_mode: FilterMode,
):
    if network not in ["mainnet", "testnet"]:
        raise Exception("Invalid network, pick mainnet or testnet")

    chunk_size = 1000
    offset = 0
    predictions: List[Prediction] = []

    # Convert filters to lowercase
    filters = [f.lower() for f in filters]

    # pylint: disable=line-too-long
    if filter_mode == FilterMode.CONTRACT:
        where_clause = f"where: {{slot_: {{predictContract_in: {json.dumps(filters)}, slot_gt: {start_ts}, slot_lt: {end_ts}}}}}"
    elif filter_mode == FilterMode.PREDICTOOR:
        where_clause = f"where: {{user_: {{id_in: {json.dumps(filters)}}}, slot_: {{slot_gt: {start_ts}, slot_lt: {end_ts}}}}}"

    while True:
        query = f"""
            {{
                predictPredictions(skip: {offset}, first: {chunk_size}, {where_clause}) {{
                    id
                    user {{
                        id
                    }}
                    stake
                    payout {{
                        payout
                        trueValue
                        predictedValue
                    }}
                    slot {{
                        slot
                        predictContract {{
                            id
                            token {{
                                id
                                name
                                nft{{
                                    nftData {{
                                    key
                                    value
                                    }}
                                }}
                            }}
                        }}
                    }}
                }}
            }}"""

        # print("Querying subgraph...", query)
        result = query_subgraph(
            get_subgraph_url(network),
            query,
            timeout=20.0,
        )

        offset += chunk_size

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


def get_all_contracts(owner_address: str, network: str) -> List[str]:
    if network != "mainnet" and network != "testnet":
        raise Exception("Invalid network, pick mainnet or testnet")

    # Define the GraphQL query
    query = (
        """
        {
            tokens(where: {
                nft_: {
                    owner: "%s"
                }
            }) {
                id
            }
        }
        """
        % owner_address
    )

    # Define the subgraph endpoint
    result = query_subgraph(get_subgraph_url(network), query, timeout=20.0)

    if not "data" in result:
        raise Exception("Error fetching contracts: No data returned")

    # Parse the results and construct Contract objects
    contract_data = result["data"]["tokens"]
    contracts = [contract["id"] for contract in contract_data]

    return contracts
