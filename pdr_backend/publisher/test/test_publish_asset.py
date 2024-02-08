from enforce_typing import enforce_types
from pytest import approx

from pdr_backend.contract.predictoor_contract import PredictoorContract
from pdr_backend.publisher.publish_asset import publish_asset


@enforce_types
def test_publish_asset(web3_pp, web3_config):
    base = "ETH"
    quote = "USDT"
    source = "kraken"
    timeframe = "5m"
    seconds_per_epoch = 300
    seconds_per_subscription = 60 * 60 * 24
    nft_data, _, _, _, logs_erc = publish_asset(
        s_per_epoch=seconds_per_epoch,
        s_per_subscription=seconds_per_subscription,
        base=base,
        quote=quote,
        source=source,
        timeframe=timeframe,
        trueval_submitter_addr=web3_config.owner,
        feeCollector_addr=web3_config.owner,
        rate=3,
        cut=0.2,
        web3_pp=web3_pp,
    )
    nft_name = base + "-" + quote + "-" + source + "-" + timeframe
    nft_symbol = base + "/" + quote
    assert nft_data == (nft_name, nft_symbol, 1, "", True, web3_config.owner)

    dt_addr = logs_erc["newTokenAddress"]
    assert web3_config.w3.is_address(dt_addr)

    contract = PredictoorContract(web3_pp, dt_addr)

    assert contract.get_secondsPerEpoch() == seconds_per_epoch
    assert (
        contract.contract_instance.functions.secondsPerSubscription().call()
        == seconds_per_subscription
    )
    assert contract.get_price() / 1e18 == approx(3 * (1.201))

    assert contract.get_stake_token() == web3_pp.OCEAN_address

    assert contract.get_trueValSubmitTimeout() == 3 * 24 * 60 * 60
