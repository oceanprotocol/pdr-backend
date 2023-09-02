"""
From this ref...
https://github.com/oceanprotocol/ocean-subgraph/pull/678 "Predictoor support")
... here's an example query:

query {
  predictContracts{
    id	
    token{
      name
    }
    secondsPerEpoch
    secondsPerSubscription
    truevalSubmitTimeout
    block
    eventIndex
    slots{
      id
      predictions{
        id
        user {
          id
        }
        stake
        payout {
          id
          predictedValue
          trueValue
          payout
        }
      }
      trueValues{
        trueValue
        txId
      }
      revenue
      revenues{
        
        amount
        txId
      }
      
      
    }
    subscriptions{
      
      user {
        id
      }
      expireTime
      txId
    }
    }
    
 }
"""

from typing import Optional, Dict, List

from enforce_typing import enforce_types
import requests
from web3 import Web3

from pdr_backend.models.feed import Feed
from pdr_backend.models.slot import Slot

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
def query_subgraph(subgraph_url: str, query: str) -> Dict[str, dict]:
    """
    @arguments
      subgraph_url -- e.g. http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph/graphql # pylint: disable=line-too-long
      query -- e.g. in docstring above

    @return
      result -- e.g. {"data" : {"predictContracts": ..}}
    """
    request = requests.post(subgraph_url, "", json={"query": query}, timeout=1.5)
    if request.status_code != 200:
        # pylint: disable=broad-exception-raised
        raise Exception(
            f"Query failed. Url: {subgraph_url}. Return code is {request.status_code}\n{query}"
        )
    result = request.json()
    return result


def query_pending_payouts(subgraph_url: str, addr: str) -> List[int]:
    chunk_size = 1000
    offset = 0
    timestamps: List[int] = []

    while True:
        query = """
        {
                predictPredictions(
                    where: {user: "%s", payout: null}
                ) {
                    id
                    timestamp
                }
        }
        """ % (
            addr
        )

        offset += chunk_size
        try:
            result = query_subgraph(subgraph_url, query)
            if not "data" in result:
                print("No data in result")
                break
            predict_predictions = result["data"]["predictPredictions"]
            timestamps_query = [i["timestamp"] for i in predict_predictions]
            timestamps.extend(timestamps_query)
        except Exception as e:
            print("An error occured", e)

    return timestamps


def query_feed_contracts(  # pylint: disable=too-many-statements
    subgraph_url: str,
    pairs: Optional[List[str]] = None,
    timeframes: Optional[List[str]] = None,
    sources: Optional[List[str]] = None,
    owners: Optional[List[str]] = None,
) -> Dict[str, dict]:
    """
    @description
      Query the chain for prediction feed contracts, then filter down
      according to pairs, timeframes, sources, or owners.

    @arguments
      subgraph_url -- e.g.
      pairs -- E.g. filter to "BTC/USDT,ETH/USDT". If None, allow all
      timeframes -- E.g. filter to "5m,15m". If None, allow all
      sources -- E.g. filter to "binance,kraken". If None, allow all
      owners -- E.g. filter to "0x123,0x124". If None, allow all

    @return
      contracts -- dict of [contract_id] : contract_info
        where contract_info is a dict with fields name, address, symbol, ..
    """
    chunk_size = 1000  # max for subgraph = 1000
    offset = 0
    feed_dicts = {}

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
                info725 = contract["token"]["nft"]["nftData"]
                info = info_from_725(info725)  # {"pair": "ETH/USDT", "base":...}

                # filter out unwanted
                owner_id = contract["token"]["nft"]["owner"]["id"]
                if owners and (owner_id not in owners):
                    continue

                pair = info["pair"]
                if pair and pairs and (pair not in pairs):
                    continue

                timeframe = info["timeframe"]
                if timeframe and timeframes and (timeframe not in timeframes):
                    continue

                source = info["source"]
                if source and sources and (source not in sources):
                    continue

                # ok, add this one
                addr = contract["id"]
                feed_dict = {
                    "name": contract["token"]["name"],
                    "address": contract["id"],
                    "symbol": contract["token"]["symbol"],
                    "seconds_per_epoch": contract["secondsPerEpoch"],
                    "seconds_per_subscription": contract["secondsPerSubscription"],
                    "last_submited_epoch": 0,
                }
                feed_dict.update(info)
                feed_dicts[addr] = feed_dict

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

    return feed_dicts


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

    while True:
        query = """
        {
            predictSlots(where: {slot_lte: %s}, skip:%s, first:%s, where: { status: "Pending" }){
                id
                slot
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
                timestamp = slot["slot"]
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
                    seconds_per_epoch=int(contract["secondsPerEpoch"]),
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
