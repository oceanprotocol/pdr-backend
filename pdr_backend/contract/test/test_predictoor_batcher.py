from unittest.mock import Mock

from enforce_typing import enforce_types
from web3.types import RPCEndpoint

from pdr_backend.conftest_ganache import S_PER_EPOCH
from pdr_backend.contract.data_nft import DataNft
from pdr_backend.contract.predictoor_batcher import mock_predictoor_batcher
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.util.currency_types import Wei


@enforce_types
def test_submit_truevals(feed_contract1, web3_pp, predictoor_batcher):
    web3_config = web3_pp.web3_config
    current_epoch = feed_contract1.get_current_epoch_ts()

    # fast forward time
    web3_config.w3.provider.make_request(
        RPCEndpoint("evm_increaseTime"), [S_PER_EPOCH * 10]
    )
    web3_config.w3.provider.make_request(RPCEndpoint("evm_mine"), [])

    end_epoch = current_epoch + S_PER_EPOCH * 10

    # get trueval for epochs
    epochs = list(range(current_epoch, end_epoch, S_PER_EPOCH))
    truevals = [True] * len(epochs)
    cancels = [False] * len(epochs)

    # add predictoor helper as ercdeployer
    erc721addr = feed_contract1.erc721_addr()
    datanft = DataNft(web3_pp, erc721addr)
    datanft.add_to_create_erc20_list(predictoor_batcher.contract_address)

    truevals_before = [
        feed_contract1.contract_instance.functions.trueValues(i).call()
        for i in epochs
    ]
    for trueval in truevals_before:
        assert trueval is False

    predictoor_batcher.submit_truevals(
        feed_contract1.contract_address, epochs, truevals, cancels
    )

    truevals_after = [
        feed_contract1.contract_instance.functions.trueValues(i).call()
        for i in epochs
    ]
    for trueval in truevals_after:
        assert trueval is True


@enforce_types
def test_submit_truevals_contracts(
    feed_contract1,
    feed_contract2,
    web3_pp,
    web3_config,
    predictoor_batcher,
):
    current_epoch = feed_contract1.get_current_epoch_ts()

    # fast forward time
    web3_config.w3.provider.make_request(
        RPCEndpoint("evm_increaseTime"), [S_PER_EPOCH * 10]
    )
    web3_config.w3.provider.make_request(RPCEndpoint("evm_mine"), [])

    end_epoch = current_epoch + S_PER_EPOCH * 10

    # get trueval for epochs
    epochs1 = list(range(current_epoch, end_epoch, S_PER_EPOCH))
    epochs2 = list(range(current_epoch + S_PER_EPOCH * 2, end_epoch, S_PER_EPOCH))
    epochs = [epochs1, epochs2]
    truevals = [[True] * len(epochs1), [True] * len(epochs2)]
    cancels = [[False] * len(epochs1), [False] * len(epochs2)]
    addresses = [
        feed_contract1.contract_address,
        feed_contract2.contract_address,
    ]

    # add predictoor helper as ercdeployer
    erc721addr = feed_contract1.erc721_addr()
    datanft = DataNft(web3_pp, erc721addr)
    datanft.add_to_create_erc20_list(predictoor_batcher.contract_address)
    erc721addr = feed_contract2.erc721_addr()
    datanft = DataNft(web3_pp, erc721addr)
    datanft.add_to_create_erc20_list(predictoor_batcher.contract_address)

    truevals_before_1 = [
        feed_contract1.contract_instance.functions.trueValues(i).call()
        for i in epochs1
    ]

    truevals_before_2 = [
        feed_contract2.contract_instance.functions.trueValues(i).call()
        for i in epochs1
    ]

    for trueval in truevals_before_1:
        assert trueval is False

    for trueval in truevals_before_2:
        assert trueval is False

    predictoor_batcher.submit_truevals_contracts(addresses, epochs, truevals, cancels)

    truevals_after_1 = [
        feed_contract1.contract_instance.functions.trueValues(i).call()
        for i in epochs1
    ]

    truevals_after_2 = [
        feed_contract2.contract_instance.functions.trueValues(i).call()
        for i in epochs1
    ]

    for trueval in truevals_after_1:
        assert trueval is True

    for trueval in truevals_after_2[:2]:  # did not include first two epochs
        assert trueval is False

    for trueval in truevals_after_2[2:]:
        assert trueval is True


@enforce_types
def test_consume_multiple(feed_contract1, OCEAN, predictoor_batcher):
    owner = OCEAN.config.owner

    price = feed_contract1.get_price()
    print(price)

    times = 10
    cost = Wei(times * price.amt_wei)

    OCEAN.approve(predictoor_batcher.contract_address, cost)
    balance_before = OCEAN.balanceOf(owner)

    predictoor_batcher.consume_multiple(
        [feed_contract1.contract_address], [times], OCEAN.contract_address
    )

    balance_after = OCEAN.balanceOf(owner)
    assert balance_after + cost == balance_before


@enforce_types
def test_mock_predictoor_batcher():
    web3_pp = Mock(spec=Web3PP)
    b = mock_predictoor_batcher(web3_pp)
    assert id(b.web3_pp) == id(web3_pp)
    assert b.contract_address == "0xPdrBatcherAddr"
