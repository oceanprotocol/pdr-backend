from typing import List, TypedDict
import json
from enum import Enum
from enforce_typing import enforce_types

from pdr_backend.util.subgraph import query_subgraph, info_from_725
from pdr_backend.models.prediction import Prediction
from pdr_backend.util.networkutil import get_subgraph_url


class ContractIdAndSPE(TypedDict):
    id: str
    seconds_per_epoch: int


class FilterMode(Enum):
    CONTRACT = 1
    PREDICTOOR = 2


@enforce_types
def fetch_filtered_predictions(
    start_ts: int,
    end_ts: int,
    filters: List[str],
    network: str,
    filter_mode: FilterMode,
) -> List[Prediction]:
    """
    Fetches predictions from a subgraph within a specified time range
    and according to given filters.

    This function supports querying predictions based on contract
    addresses or predictor addresses, depending on the filter mode.
    It iteratively queries the subgraph in chunks to retrieve all relevant
    predictions and constructs Prediction objects from the results.

    Args:
        start_ts: The starting Unix timestamp for the query range.
        end_ts: The ending Unix timestamp for the query range.
        filters: A list of strings representing the filter
            values (contract addresses or predictor IDs).
        network: A string indicating the blockchain network to query ('mainnet' or 'testnet').
        filter_mode: An instance of FilterMode indicating whether to filter
            by contract or by predictor.

    Returns:
        A list of Prediction objects that match the filter criteria within the given time range.

    Raises:
        Exception: If the specified network is neither 'mainnet' nor 'testnet'.
    """

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

        print("Querying subgraph...", query)
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


@enforce_types
def get_all_contract_ids_by_owner(owner_address: str, network: str) -> List[str]:
    """
    Retrieves a list of contract IDs owned by the specified address on a given network.

    This function queries a subgraph for all tokens (interpreted as contracts in this context)
    owned by the provided owner address. It supports queries on both the mainnet and testnet
    networks. The function raises an exception if an invalid network is specified or if no data
    is returned from the subgraph.

    Args:
        owner_address: The blockchain address of the owner whose contract IDs are to be retrieved.
        network: A string indicating the blockchain network to query ('mainnet' or 'testnet').

    Returns:
        A list of strings, where each string is a contract ID associated with the owner address.

    Raises:
        Exception: If the specified network is neither 'mainnet' nor 'testnet', or if the query
        to the subgraph does not return any data.
    """

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


@enforce_types
def fetch_contract_id_and_spe(
    contract_addresses: List[str], network: str
) -> List[ContractIdAndSPE]:
    """
    This function queries a GraphQL endpoint to retrieve contract details such as
    the contract ID and seconds per epoch for each contract address provided.
    It supports querying both mainnet and testnet networks.

    Args:
        contract_addresses (List[str]): A list of contract addresses to query.
        network (str): The blockchain network to query ('mainnet' or 'testnet').

    Raises:
        Exception: If the network is not 'mainnet' or 'testnet', or if no data is returned.

    Returns:
        List[ContractDetail]: A list of dictionaries containing contract details.
    """

    if network not in ("mainnet", "testnet"):
        raise Exception("Invalid network, pick mainnet or testnet")

    # Define the GraphQL query
    query = """
        {
            predictContracts(where: {
                id_in: %s
            }){
                id
                secondsPerEpoch
            }
        }
        """ % json.dumps(
        contract_addresses
    )

    # Define the subgraph endpoint and query it
    result = query_subgraph(get_subgraph_url(network), query, timeout=20.0)

    if "data" not in result:
        raise Exception("Error fetching contracts: No data returned")

    # Parse the results and construct ContractDetail objects
    contract_data = result["data"]["predictContracts"]
    contracts: List[ContractIdAndSPE] = [
        {"id": contract["id"], "seconds_per_epoch": contract["secondsPerEpoch"]}
        for contract in contract_data
    ]

    return contracts
