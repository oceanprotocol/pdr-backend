import json
from enum import Enum
import logging
from typing import List, TypedDict

from enforce_typing import enforce_types

from pdr_backend.subgraph.prediction import Prediction
from pdr_backend.subgraph.core_subgraph import query_subgraph
from pdr_backend.subgraph.info725 import info725_to_info
from pdr_backend.util.networkutil import get_subgraph_url
from pdr_backend.util.time_types import UnixTimeS

logger = logging.getLogger("subgraph")


class ContractIdAndSPE(TypedDict):
    ID: str
    seconds_per_epoch: int
    name: str


class FilterMode(Enum):
    NONE = 0
    CONTRACT = 1
    PREDICTOOR = 2
    CONTRACT_TS = 3


# pylint: disable=too-many-statements
@enforce_types
def fetch_filtered_predictions(
    start_ts: UnixTimeS,
    end_ts: UnixTimeS,
    addresses: List[str],
    first: int,
    skip: int,
    network: str = "mainnet",
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
        addresses: A list of strings representing the filter
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

    predictions: List[Prediction] = []

    # Convert filters to lowercase
    filters = [f.lower() for f in addresses]

    # pylint: disable=line-too-long
    where_clause = f", where: {{timestamp_gt: {start_ts}, timestamp_lt: {end_ts}, slot_: {{predictContract_in: {json.dumps(filters)}}}}}"

    query = f"""
        {{
            predictPredictions(skip: {skip}, first: {first} {where_clause}) {{
                id
                timestamp
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

    try:
        logger.info("Querying subgraph... %s", query)
        result = query_subgraph(
            get_subgraph_url(network),
            query,
            timeout=20.0,
        )
    except Exception as e:
        logger.warning(
            "Error fetching predictPredictions, got #%d items. Exception: %s",
            len(predictions),
            e,
        )

    if "data" not in result or not result["data"]:
        return []

    data = result["data"].get("predictPredictions", [])
    if len(data) == 0:
        return []

    for prediction_sg_dict in data:
        info725 = prediction_sg_dict["slot"]["predictContract"]["token"]["nft"][
            "nftData"
        ]
        info = info725_to_info(info725)
        pair = info["pair"]
        timeframe = info["timeframe"]
        source = info["source"]
        timestamp = UnixTimeS(int(prediction_sg_dict["timestamp"]))
        slot = UnixTimeS(int(prediction_sg_dict["slot"]["slot"]))
        user = prediction_sg_dict["user"]["id"]
        address = prediction_sg_dict["id"].split("-")[0]
        trueval = None
        payout = None
        predicted_value = None
        stake = None

        if not prediction_sg_dict["payout"] is None:
            stake = float(prediction_sg_dict["stake"])
            trueval = prediction_sg_dict["payout"]["trueValue"]
            predicted_value = prediction_sg_dict["payout"]["predictedValue"]
            payout = float(prediction_sg_dict["payout"]["payout"])

        prediction = Prediction(
            ID=prediction_sg_dict["id"],
            contract=address,
            pair=pair,
            timeframe=timeframe,
            prediction=predicted_value,
            stake=stake,
            trueval=trueval,
            timestamp=timestamp,
            source=source,
            payout=payout,
            slot=slot,
            user=user,
        )
        predictions.append(prediction)

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
    @description
      Query a GraphQL endpoint to retrieve details of contracts, like
      contract ID and seconds per epoch.

    @arguments
        contract_addresses - contract addresses to query
        network - where to query. Eg 'mainnet' or 'testnet'

    @return
        contracts_list - where each item has contract details
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
                token {
                    name
                }
            }
        }
        """ % json.dumps(
        contract_addresses
    )

    # Define the subgraph endpoint and query it
    result = query_subgraph(get_subgraph_url(network), query, timeout=20.0)

    if "data" not in result:
        raise Exception("Error fetching contracts: No data returned")

    contracts_sg_dict = result["data"]["predictContracts"]

    contracts_list: List[ContractIdAndSPE] = []
    for contract_sg_dict in contracts_sg_dict:
        contract_item: ContractIdAndSPE = {
            "ID": contract_sg_dict["id"],
            "seconds_per_epoch": contract_sg_dict["secondsPerEpoch"],
            "name": contract_sg_dict["token"]["name"],
        }
        contracts_list.append(contract_item)

    return contracts_list
