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
    blocksPerEpoch
    blocksPerSubscription
    truevalSubmitTimeoutBlock
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
        floatValue
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


import os
import requests
from typing import Optional, Dict

from enforce_typing import enforce_types
from web3 import Web3

@enforce_types
def key_to_725(key:str):
    key725 = Web3.keccak(key.encode("utf-8")).hex()
    return key725


@enforce_types
def value_to_725(value:str):
    value725 = Web3.to_hex(text=value)
    return value725


@enforce_types
def value_from_725(value725) -> str:
    value = Web3.to_text(hexstr=value725)
    return value


@enforce_types
def info_from_725(info725_list: list) -> Dict[str, str]:
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
    target_keys = ["pair", "base", "quote", "source", "timeframe"]
    info_dict = {}
    for key in target_keys:
        for item725 in info725_list:
            key725 = item725["key"]
            value725 = item725["value"]
            if key725 == key_to_725(key):
                value = value_from_725(value725)
                info_dict[key] = value
                break

    return info_dict


@enforce_types
def query_subgraph(subgraph_url:str, query:str) -> Dict[str, dict]:
    """
    @arguments
      subgraph_url -- e.g. http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph/graphql
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


@enforce_types
def get_all_interesting_prediction_contracts(
        subgraph_url:str,
        pairs:Optional[str]=None,
        timeframes:Optional[str]=None,
        sources:Optional[str]=None,
        owners:Optional[str]=None,
) -> Dict[str, dict]:
    """
    @description
      Query the chain for prediction contracts, then filter down 
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
    contracts = {}
    
    # prepare keys
    owners_filter, pairs_filter, timeframes_filter, sources_filter = \
        [], [], [], []
    
    if owners:
        owners_filter = [owner.lower() for owner in owners.split(",")]
    if pairs:
        pairs_filter = [pair for pair in pairs.split(",") if pairs]
    if timeframes:
        timeframes_filter = [
            timeframe for timeframe in timeframes.split(",") if timeframes
        ]
    if sources:
        sources_filter = [source for source in sources.split(",") if sources]

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
                blocksPerEpoch
                blocksPerSubscription
                truevalSubmitTimeoutBlock
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
            if contract_list == []:
                break
            for contract in contract_list:
                info725 = contract["token"]["nft"]["nftData"]
                
                # dict of {"pair": "ETH/USDT", "base":...}
                info = info_from_725(info725)
                            
                # now do filtering
                if (
                    (
                        len(owners_filter) > 0
                        and contract["token"]["nft"]["owner"]["id"] not in owners_filter
                    )
                    or (
                        len(pairs_filter) > 0
                        and info["pair"]
                        and info["pair"] not in pairs_filter
                    )
                    or (
                        len(timeframes_filter) > 0
                        and info["timeframe"]
                        and info["timeframe"] not in timeframes_filter
                    )
                    or (
                        len(sources_filter) > 0
                        and info["source"]
                        and info["source"] not in sources_filter
                    )
                ):
                    continue

                contracts[contract["id"]] = {
                    "name": contract["token"]["name"],
                    "address": contract["id"],
                    "symbol": contract["token"]["symbol"],
                    "blocks_per_epoch": contract["blocksPerEpoch"],
                    "blocks_per_subscription": contract["blocksPerSubscription"],
                    "last_submited_epoch": 0,
                }
                contracts[contract["id"]].update(info)
        except Exception as e:
            print(e)
            return {}
    return contracts
