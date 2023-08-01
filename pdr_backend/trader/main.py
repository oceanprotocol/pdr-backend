import time
import os


from pdr_utils.subgraph import get_all_interesting_prediction_contracts
from pdr_utils.contract import PredictorContract, Web3Config
from trade import trade

# TODO - check for all envs
assert os.environ.get("RPC_URL", None), "You must set RPC_URL environment variable"
assert os.environ.get(
    "SUBGRAPH_URL", None
), "You must set SUBGRAPH_URL environment variable"
web3_config = Web3Config(os.environ.get("RPC_URL"), os.environ.get("PRIVATE_KEY"))
owner = web3_config.owner


""" Get all intresting topics that we can predict.  Like ETH-USDT, BTC-USDT """
topics = []


def process_block(block):
    global topics
    """ Process each contract and see if we need to submit """
    if not topics:
        topics = get_all_interesting_prediction_contracts(
            os.environ.get("SUBGRAPH_URL"),
            os.environ.get("PAIR_FILTER", None),
            os.environ.get("TIMEFRAME_FILTER", None),
            os.environ.get("SOURCE_FILTER", None),
            os.environ.get("OWNER_ADDRS", None),
        )
    print(f"Got new block: {block['number']} with {len(topics)} topics")
    for address in topics:
        topic = topics[address]
        predictor_contract = PredictorContract(web3_config, address)
        epoch = predictor_contract.get_current_epoch()
        blocks_per_epoch = predictor_contract.get_blocksPerEpoch()
        blocks_till_epoch_end = (
            epoch * blocks_per_epoch + blocks_per_epoch - block["number"]
        )
        print(
            f"\t{topic['name']} (at address {topic['address']} is at epoch {epoch}, blocks_per_epoch: {blocks_per_epoch}, blocks_till_epoch_end: {blocks_till_epoch_end}"
        )
        if epoch > topic["last_submited_epoch"] and epoch > 0:
            topic["last_submited_epoch"] = epoch
            print(f"Read new prediction")
            """ Let's get the prediction and trade it """
            prediction = predictor_contract.get_agg_predval(block["number"])
            print(f"Got {prediction}.")
            if prediction is not None:
                trade(topic, prediction)


def main():
    print("Starting main loop...")
    lastblock = 0
    while True:
        block = web3_config.w3.eth.block_number
        if block > lastblock:
            lastblock = block
            process_block(web3_config.w3.eth.get_block(block, full_transactions=False))
        else:
            time.sleep(1)


if __name__ == "__main__":
    main()
