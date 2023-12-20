from unittest.mock import Mock

from enforce_typing import enforce_types
from web3.types import RPCEndpoint

from pdr_backend.conftest_ganache import S_PER_EPOCH
from pdr_backend.contract.data_nft import DataNft
from pdr_backend.contract.predictoor_batcher import mock_predictoor_batcher
from pdr_backend.ppss.web3_pp import Web3PP


@enforce_types
def test_submit_truevals(predictoor_contract, web3_pp, predictoor_batcher):
    web3_config = web3_pp.web3_config
    current_epoch = predictoor_contract.get_current_epoch_ts()

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
    erc721addr = predictoor_contract.erc721_addr()
    datanft = DataNft(web3_pp, erc721addr)
    datanft.add_to_create_erc20_list(predictoor_batcher.contract_address)

    truevals_before = [
        predictoor_contract.contract_instance.functions.trueValues(i).call()
        for i in epochs
    ]
    for trueval in truevals_before:
        assert trueval is False

    predictoor_batcher.submit_truevals(
        predictoor_contract.contract_address, epochs, truevals, cancels
    )

    truevals_after = [
        predictoor_contract.contract_instance.functions.trueValues(i).call()
        for i in epochs
    ]
    for trueval in truevals_after:
        assert trueval is True


@enforce_types
def test_submit_truevals_contracts(
    predictoor_contract,
    predictoor_contract2,
    web3_pp,
    web3_config,
    predictoor_batcher,
):
    current_epoch = predictoor_contract.get_current_epoch_ts()

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
        predictoor_contract.contract_address,
        predictoor_contract2.contract_address,
    ]

    # add predictoor helper as ercdeployer
    erc721addr = predictoor_contract.erc721_addr()
    datanft = DataNft(web3_pp, erc721addr)
    datanft.add_to_create_erc20_list(predictoor_batcher.contract_address)
    erc721addr = predictoor_contract2.erc721_addr()
    datanft = DataNft(web3_pp, erc721addr)
    datanft.add_to_create_erc20_list(predictoor_batcher.contract_address)

    truevals_before_1 = [
        predictoor_contract.contract_instance.functions.trueValues(i).call()
        for i in epochs1
    ]

    truevals_before_2 = [
        predictoor_contract2.contract_instance.functions.trueValues(i).call()
        for i in epochs1
    ]

    for trueval in truevals_before_1:
        assert trueval is False

    for trueval in truevals_before_2:
        assert trueval is False

    predictoor_batcher.submit_truevals_contracts(addresses, epochs, truevals, cancels)

    truevals_after_1 = [
        predictoor_contract.contract_instance.functions.trueValues(i).call()
        for i in epochs1
    ]

    truevals_after_2 = [
        predictoor_contract2.contract_instance.functions.trueValues(i).call()
        for i in epochs1
    ]

    for trueval in truevals_after_1:
        assert trueval is True

    for trueval in truevals_after_2[:2]:  # did not include first two epochs
        assert trueval is False

    for trueval in truevals_after_2[2:]:
        assert trueval is True


@enforce_types
def test_consume_multiple(predictoor_contract, ocean_token, predictoor_batcher):
    owner = ocean_token.config.owner

    price = predictoor_contract.get_price()
    print(price)

    times = 10
    cost = times * price

    ocean_token.approve(predictoor_batcher.contract_address, cost)
    balance_before = ocean_token.balanceOf(owner)

    predictoor_batcher.consume_multiple(
        [predictoor_contract.contract_address], [times], ocean_token.contract_address
    )

    balance_after = ocean_token.balanceOf(owner)
    assert balance_after + cost == balance_before


@enforce_types
def test_mock_predictoor_batcher():
    web3_pp = Mock(spec=Web3PP)
    b = mock_predictoor_batcher(web3_pp)
    assert id(b.web3_pp) == id(web3_pp)
    assert b.contract_address == "0xPdrBatcherAddr"
