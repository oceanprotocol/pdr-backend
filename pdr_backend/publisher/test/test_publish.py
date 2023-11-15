# comment out until more fleshed out
# from pdr_backend.publisher.publish import fund_dev_accounts, publish


import os
from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.publisher.publish import publish
from pdr_backend.util.contract import get_address
from pdr_backend.util.web3_config import Web3Config


def test_publisher_publish():
    config = Web3Config(os.getenv("RPC_URL"), os.getenv("PRIVATE_KEY"))
    base = "ETH"
    quote = "USDT"
    source = "kraken"
    timeframe = "5m"
    seconds_per_epoch = 360
    seconds_per_subscription = 1000
    nft_data, _, _, _, logs_erc = publish(
        s_per_epoch=seconds_per_epoch,
        s_per_subscription=seconds_per_subscription,
        base=base,
        quote=quote,
        source=source,
        timeframe=timeframe,
        trueval_submitter_addr=config.owner,
        feeCollector_addr=config.owner,
        rate=3,
        cut=0.2,
        web3_config=config,
    )
    nft_name = base + "-" + quote + "-" + source + "-" + timeframe
    nft_symbol = base + "/" + quote
    assert nft_data == (nft_name, nft_symbol, 1, "", True, config.owner)

    dt_addr = logs_erc["newTokenAddress"]
    assert config.w3.is_address(dt_addr)

    contract = PredictoorContract(config, dt_addr)

    assert contract.get_secondsPerEpoch() == seconds_per_epoch
    assert (
        contract.contract_instance.functions.secondsPerSubscription().call()
        == seconds_per_subscription
    )
    assert contract.get_price() == 3

    ocean_address = get_address(config.w3.eth.chain_id, "Ocean")
    assert contract.get_stake_token() == ocean_address

    assert contract.get_trueValSubmitTimeout() == 3 * 24 * 60 * 60
