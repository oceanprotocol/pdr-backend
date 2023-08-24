from typing import List, Optional
from pdr_backend.util.web3_config import Web3Config
from pdr_backend.util.subgraph import query_subgraph, info_from_725
from pdr_backend.models.contract_data import ContractData
from pdr_backend.models.slot import Slot


def get_pending_slots(subgraph_url: str, web3_config: Web3Config):
    timestamp = web3_config.w3.eth.get_block("latest")["timestamp"]
    chunk_size = 1000
    offset = 0
    owners: List[str] = []  # TODO: add owners

    slots: List[Slot] = []

    while True:
        query = """
        {
            predictSlots(where: {slot_lte: %s}, skip:%s, first:%s, where: { truevalSubmitted: false }){
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

                owner_id = contract["token"]["nft"]["owner"]["id"]
                if len(owners) > 0 and (owner_id not in owners):
                    continue

                contract_object = ContractData(
                    name=contract["token"]["name"],
                    address=contract["id"],
                    symbol=contract["token"]["symbol"],
                    seconds_per_epoch=contract["secondsPerEpoch"],
                    seconds_per_subscription=contract["secondsPerSubscription"],
                    trueval_submit_timeout=contract["truevalSubmitTimeout"],
                    owner=contract["token"]["nft"]["owner"]["id"],
                    pair=info["pair"],
                    timeframe=info["timeframe"],
                    source=info["source"],
                )

                slots.append(Slot(int(slot["slot"]), contract_object))

        except Exception as e:
            print(e)
            break

    return slots
