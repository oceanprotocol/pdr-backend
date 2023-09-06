import time
from os import getenv
from pdr_backend.util.subgraph import query_subgraph


subgraph_url=getenv("SUBGRAPH_URL","https://v4.subgraph.sapphire-testnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph")
predictoor1_address=getenv("PREDICTOOR1_ADDRESS","0x005c414442a892077bd2c1d62b1de2fc127e5b9b")


ts = int(time.time())
query = """
        {
            predictContracts{
                id
                token{
                    name
                }
                subscriptions(orderBy: expireTime orderDirection:desc first:10){
                    user {
                        id
                    }
                    expireTime
                }
                slots(where:{slot_lt:%s} orderBy: slot orderDirection:desc first:288){
                    slot
                    roundSumStakesUp
                    roundSumStakes
                    predictions(orderBy: timestamp orderDirection:desc){
                        stake
                        user {
                            id
                        }
                        timestamp
                        payout{
                            payout
                            predictedValue
                            trueValue
                        }
                    }
                    trueValues{
                        trueValue
                    }
                }
            } 
        }
        """ % (
            ts,
        )
result = query_subgraph(subgraph_url, query)
#check no of contracts
no_of_contracts = len(result["data"]["predictContracts"])
if no_of_contracts>=11:
    print(f"Number of Predictoor contracts: {no_of_contracts} - OK")
else:
    print(f"Number of Predictoor contracts: {no_of_contracts} - FAILED")
#check number of predictions
print("Checking number of predictions:")
for contract in result["data"]["predictContracts"]:
    got_pred=True
    count = 0
    with_preds = 0
    for slot in contract['slots']:
        count=count+1
        if len(slot["predictions"])>0:
            with_preds=with_preds+1
    if with_preds/count>0.9:
        print(f"\t For {contract['token']['name']} , we found {with_preds} predictions for {contract['token']['name']} from a total of {count} slots - OK")
    else:
        print(f"\t For {contract['token']['name']} , we found {with_preds} predictions for {contract['token']['name']} from a total of {count} slots - FAILED")
#check number of truevals
print("Checking number of Truevals:")
for contract in result["data"]["predictContracts"]:
    got_pred=True
    count = 0
    with_preds = 0
    for slot in contract['slots']:
        count=count+1
        if len(slot["trueValues"])>0:
            with_preds=with_preds+1
    if with_preds/count>0.9:
        print(f"\t For {contract['token']['name']} , we found {with_preds} truevals for {contract['token']['name']} from a total of {count} slots - OK")
    else:
        print(f"\t For {contract['token']['name']} , we found {with_preds} truevals for {contract['token']['name']} from a total of {count} slots - FAILED")
