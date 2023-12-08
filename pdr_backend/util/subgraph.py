"""
- READMEs/subgraph.md describes usage of Predictoor subgraph, with an example query
- the functions below provide other specific examples, that are used by agents of pdr-backend
"""
import time
from collections import defaultdict
from typing import Optional, Dict, List

from enforce_typing import enforce_types
import requests
from web3 import Web3

from pdr_backend.util.constants import SUBGRAPH_MAX_TRIES
from pdr_backend.models.feed import Feed
from pdr_backend.models.slot import Slot
from pdr_backend.util.web3_config import Web3Config

_N_ERRORS = {}  # exception_str : num_occurrences
_N_THR = 3


@enforce_types
def key_to_725(key: str):
    key725 = Web3.keccak(key.encode("utf-8")).hex()
    return key725


@enforce_types
def value_to_725(value: str):
    value725 = Web3.to_hex(text=value)
    return value725


@enforce_types
def value_from_725(value725) -> str:
    value = Web3.to_text(hexstr=value725)
    return value


@enforce_types
def info_from_725(info725_list: list) -> Dict[str, Optional[str]]:
    """
    @arguments
      info725_list -- eg [{"key":encoded("pair"), "value":encoded("ETH/USDT")},
                          {"key":encoded("timeframe"), "value":encoded("5m") },
                           ... ]
    @return
      info_dict -- e.g. {"pair": "ETH/USDT",
                         "timeframe": "5m",
                          ... }
    """
    target_keys = ["pair", "timeframe", "source", "base", "quote"]
    info_dict: Dict[str, Optional[str]] = {}
    for key in target_keys:
        info_dict[key] = None
        for item725 in info725_list:
            key725, value725 = item725["key"], item725["value"]
            if key725 == key_to_725(key):
                value = value_from_725(value725)
                info_dict[key] = value
                break

    return info_dict


@enforce_types
def query_subgraph(
    subgraph_url: str, query: str, tries: int = 3, timeout: float = 30.0
) -> Dict[str, dict]:
    """
    @arguments
      subgraph_url -- e.g. http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph # pylint: disable=line-too-long
      query -- e.g. in docstring above

    @return
      result -- e.g. {"data" : {"predictContracts": ..}}
    """
    request = requests.post(subgraph_url, "", json={"query": query}, timeout=timeout)
    if request.status_code != 200:
        # pylint: disable=broad-exception-raised
        if tries < SUBGRAPH_MAX_TRIES:
            return query_subgraph(subgraph_url, query, tries + 1)
        raise Exception(
            f"Query failed. Url: {subgraph_url}. Return code is {request.status_code}\n{query}"
        )
    result = request.json()
    return result


@enforce_types
def query_pending_payouts(subgraph_url: str, addr: str) -> Dict[str, List[int]]:
    chunk_size = 1000
    offset = 0
    pending_slots: Dict[str, List[int]] = {}
    addr = addr.lower()

    while True:
        query = """
        {
                predictPredictions(
                    where: {user: "%s", payout: null}, first: %s, skip: %s
                ) {
                    id
                    timestamp
                    slot {
                        id
                        slot
                        predictContract {
                            id
                        }
                    }
                }
        }
        """ % (
            addr,
            chunk_size,
            offset,
        )
        offset += chunk_size
        print(".", end="", flush=True)
        try:
            result = query_subgraph(subgraph_url, query)
            if not "data" in result or len(result["data"]) == 0:
                print("No data in result")
                break
            predict_predictions = result["data"]["predictPredictions"]
            if len(predict_predictions) == 0:
                break
            for prediction in predict_predictions:
                contract_address = prediction["slot"]["predictContract"]["id"]
                timestamp = prediction["slot"]["slot"]
                pending_slots.setdefault(contract_address, []).append(timestamp)
        except Exception as e:
            print("An error occured", e)

    print()  # print new line
    return pending_slots


@enforce_types
def query_feed_contracts(
    subgraph_url: str,
    owners_string: Optional[str] = None,
) -> Dict[str, Feed]:
    """
    @description
      Query the chain for prediction feed contracts.

    @arguments
      subgraph_url -- e.g.
      owners -- E.g. filter to "0x123,0x124". If None or "", allow all

    @return
      feeds -- dict of [feed_addr] : Feed
    """
    owners = None
    if owners_string:
        owners = owners_string.lower().split(",")

    chunk_size = 1000  # max for subgraph = 1000
    offset = 0
    feeds: Dict[str, Feed] = {}

    while True:
        query = """
        {
            predictContracts(skip:%s, first:%s){
                id
                token {
                    id
                    name
                    symbol
                    nft {
                        owner {
                            id
                        }
                        nftData {
                            key
                            value
                        }
                    }
                }
                secondsPerEpoch
                secondsPerSubscription
                truevalSubmitTimeout
            }
        }
        """ % (
            offset,
            chunk_size,
        )
        offset += chunk_size
        try:
            result = query_subgraph(subgraph_url, query)
            contract_list = result["data"]["predictContracts"]
            if not contract_list:
                break
            for contract in contract_list:
                _info725 = contract["token"]["nft"]["nftData"]
                _info = info_from_725(_info725)  # {"pair": "ETH/USDT", "base":...}
                pair, timeframe, source = (
                    _info["pair"],
                    _info["timeframe"],
                    _info["source"],
                )
                if None in (pair, timeframe, source):
                    continue

                # filter out unwanted
                owner_id = contract["token"]["nft"]["owner"]["id"]
                if owners and (owner_id not in owners):
                    continue

                # ok, add this one
                feed = Feed(
                    name=contract["token"]["name"],
                    address=contract["id"],
                    symbol=contract["token"]["symbol"],
                    seconds_per_subscription=int(contract["secondsPerSubscription"]),
                    trueval_submit_timeout=int(contract["truevalSubmitTimeout"]),
                    owner=owner_id,
                    pair=pair,
                    timeframe=timeframe,
                    source=source,
                )
                feeds[feed.address] = feed

        except Exception as e:
            e_str = str(e)
            e_key = e_str
            if "Connection object" in e_str:
                i = e_str.find("Connection object") + len("Connection object")
                e_key = e_key[:i]

            if e_key not in _N_ERRORS:
                _N_ERRORS[e_key] = 0
            _N_ERRORS[e_key] += 1

            if _N_ERRORS[e_key] <= _N_THR:
                print(e_str)
            if _N_ERRORS[e_key] == _N_THR:
                print("Future errors like this will be hidden")
            return {}

    # postconditions
    for feed in feeds.values():
        assert isinstance(feed, Feed)
    return feeds


def get_pending_slots(
    subgraph_url: str,
    timestamp: int,
    owner_addresses: Optional[List[str]],
    pair_filter: Optional[List[str]] = None,
    timeframe_filter: Optional[List[str]] = None,
    source_filter: Optional[List[str]] = None,
):
    chunk_size = 1000
    offset = 0
    owners: Optional[List[str]] = owner_addresses

    slots: List[Slot] = []

    now_ts = time.time()
    # rounds older than 3 days are canceled + 10 min buffer
    three_days_ago = int(now_ts - 60 * 60 * 24 * 3 + 10 * 60)

    while True:
        query = """
        {
            predictSlots(where: {slot_gt: %s, slot_lte: %s, status: "Pending"}, skip:%s, first:%s){
                id
                slot
                status
                trueValues {
                    id
                }
                predictContract {
                    id
                    token {
                        id
                        name
                        symbol
                        nft {
                            owner {
                                id
                            }
                            nftData {
                                key
                                value
                            }
                        }
                    }
                    secondsPerEpoch
                    secondsPerSubscription
                    truevalSubmitTimeout
                }
            }
        }
        """ % (
            three_days_ago,
            timestamp,
            offset,
            chunk_size,
        )

        offset += chunk_size
        try:
            result = query_subgraph(subgraph_url, query)
            if not "data" in result:
                print("No data in result")
                break
            slot_list = result["data"]["predictSlots"]
            if slot_list == []:
                break
            for slot in slot_list:
                if slot["trueValues"] != []:
                    continue

                contract = slot["predictContract"]
                info725 = contract["token"]["nft"]["nftData"]
                info = info_from_725(info725)
                assert info["pair"], "need a pair"
                assert info["timeframe"], "need a timeframe"
                assert info["source"], "need a source"

                owner_id = contract["token"]["nft"]["owner"]["id"]
                if owners and (owner_id not in owners):
                    continue

                if pair_filter and (info["pair"] not in pair_filter):
                    continue

                if timeframe_filter and (info["timeframe"] not in timeframe_filter):
                    continue

                if source_filter and (info["source"] not in source_filter):
                    continue

                feed = Feed(
                    name=contract["token"]["name"],
                    address=contract["id"],
                    symbol=contract["token"]["symbol"],
                    seconds_per_subscription=int(contract["secondsPerSubscription"]),
                    trueval_submit_timeout=int(contract["truevalSubmitTimeout"]),
                    owner=contract["token"]["nft"]["owner"]["id"],
                    pair=info["pair"],
                    timeframe=info["timeframe"],
                    source=info["source"],
                )

                slot_number = int(slot["slot"])
                slot = Slot(slot_number, feed)
                slots.append(slot)

        except Exception as e:
            print(e)
            break

    return slots


def get_consume_so_far_per_contract(
    subgraph_url: str,
    user_address: str,
    since_timestamp: int,
    contract_addresses: List[str],
) -> Dict[str, float]:
    chunk_size = 1000  # max for subgraph = 1000
    offset = 0
    consume_so_far: Dict[str, float] = defaultdict(float)
    print("Getting consume so far...")
    while True:  # pylint: disable=too-many-nested-blocks
        query = """
        {
            predictContracts(first:1000, where: {id_in: %s}){
                id	
                token{
                    id
                    name
                    symbol
                    nft {
                        owner {
                            id
                        }
                        nftData {
                            key
                            value
                        }
                    }
                    orders(where: {createdTimestamp_gt:%s, consumer_in:["%s"]}, first: %s, skip: %s){
        		        createdTimestamp
                        consumer {
                            id
                        }
                        lastPriceValue
                    }
                }
                secondsPerEpoch
                secondsPerSubscription
                truevalSubmitTimeout
            }
        }
        """ % (
            str(contract_addresses).replace("'", '"'),
            since_timestamp,
            user_address.lower(),
            chunk_size,
            offset,
        )
        offset += chunk_size
        result = query_subgraph(subgraph_url, query, 3, 30.0)
        if "data" not in result or "predictContracts" not in result["data"]:
            break
        contracts = result["data"]["predictContracts"]
        if contracts == []:
            break
        no_of_zeroes = 0
        for contract in contracts:
            contract_address = contract["id"]
            if contract_address not in contract_addresses:
                continue
            order_count = len(contract["token"]["orders"])
            if order_count == 0:
                no_of_zeroes += 1
            for buy in contract["token"]["orders"]:
                # 1.2 20% fee
                # 0.001 0.01% community swap fee
                consume_amt = float(buy["lastPriceValue"]) * 1.201
                consume_so_far[contract_address] += consume_amt
        if no_of_zeroes == len(contracts):
            break
    return consume_so_far


@enforce_types
def block_number_is_synced(subgraph_url: str, block_number: int) -> bool:
    query = """
        {
            predictContracts(block:{number:%s}){
                id
            }
        }
    """ % (
        block_number
    )
    try:
        result = query_subgraph(subgraph_url, query)
        if "errors" in result:
            return False
    except Exception as _:
        return False
    return True


@enforce_types
def wait_until_subgraph_syncs(web3_config: Web3Config, subgraph_url: str):
    block_number = web3_config.w3.eth.block_number
    while block_number_is_synced(subgraph_url, block_number) is not True:
        print("Subgraph is out of sync, trying again in 5 seconds")
        time.sleep(5)
