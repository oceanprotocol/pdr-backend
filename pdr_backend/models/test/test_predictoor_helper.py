from pdr_backend.conftest_ganache import SECONDS_PER_EPOCH
from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.models.predictoor_helper import PredictoorHelper
from pdr_backend.models.erc721 import ERC721
from pdr_backend.models.token import Token
from pdr_backend.util.contract import get_address
from pdr_backend.util.web3_config import Web3Config


def test_submit_truevals(
    predictoor_contract: PredictoorContract,
    web3_config: Web3Config,
    predictoor_helper: PredictoorHelper,
):
    current_epoch = predictoor_contract.get_current_epoch_ts()

    # fast forward time
    predictoor_contract.config.w3.provider.make_request(
        "evm_increaseTime", [SECONDS_PER_EPOCH * 10]
    )
    predictoor_contract.config.w3.provider.make_request("evm_mine", [])

    end_epoch = current_epoch + SECONDS_PER_EPOCH * 10

    # get trueval for epochs
    epochs = [i for i in range(current_epoch, end_epoch, SECONDS_PER_EPOCH)]
    truevals = [True] * len(epochs)
    cancels = [False] * len(epochs)

    # add predictoor helper as ercdeployer
    erc721addr = predictoor_contract.erc721_addr()
    erc721 = ERC721(web3_config, erc721addr)
    erc721.add_to_create_erc20_list(predictoor_helper.contract_address)

    truevals_before = [
        predictoor_contract.contract_instance.functions.trueValues(i).call()
        for i in epochs
    ]
    for trueval in truevals_before:
        assert trueval == False

    predictoor_helper.submit_truevals(
        predictoor_contract.contract_address, epochs, truevals, cancels
    )

    truevals_after = [
        predictoor_contract.contract_instance.functions.trueValues(i).call()
        for i in epochs
    ]
    for trueval in truevals_after:
        assert trueval == True


def test_submit_truevals_contracts(
    predictoor_contract: PredictoorContract,
    predictoor_contract2: PredictoorContract,
    web3_config: Web3Config,
    predictoor_helper: PredictoorHelper,
):
    current_epoch = predictoor_contract.get_current_epoch_ts()

    # fast forward time
    predictoor_contract.config.w3.provider.make_request(
        "evm_increaseTime", [SECONDS_PER_EPOCH * 10]
    )
    predictoor_contract.config.w3.provider.make_request("evm_mine", [])

    end_epoch = current_epoch + SECONDS_PER_EPOCH * 10

    # get trueval for epochs
    epochs1 = [i for i in range(current_epoch, end_epoch, SECONDS_PER_EPOCH)]
    epochs2 = [
        i
        for i in range(
            current_epoch + SECONDS_PER_EPOCH * 2, end_epoch, SECONDS_PER_EPOCH
        )
    ]
    epochs = [epochs1, epochs2]
    truevals = [[True] * len(epochs1), [True] * len(epochs2)]
    cancels = [[False] * len(epochs1), [False] * len(epochs2)]
    addresses = [
        predictoor_contract.contract_address,
        predictoor_contract2.contract_address,
    ]

    # add predictoor helper as ercdeployer
    erc721addr = predictoor_contract.erc721_addr()
    erc721 = ERC721(web3_config, erc721addr)
    erc721.add_to_create_erc20_list(predictoor_helper.contract_address)
    erc721addr = predictoor_contract2.erc721_addr()
    erc721 = ERC721(web3_config, erc721addr)
    erc721.add_to_create_erc20_list(predictoor_helper.contract_address)

    truevals_before_1 = [
        predictoor_contract.contract_instance.functions.trueValues(i).call()
        for i in epochs1
    ]

    truevals_before_2 = [
        predictoor_contract2.contract_instance.functions.trueValues(i).call()
        for i in epochs1
    ]

    for trueval in truevals_before_1:
        assert trueval == False

    for trueval in truevals_before_2:
        assert trueval == False

    print(truevals, epochs, cancels)

    predictoor_helper.submit_truevals_contracts(addresses, epochs, truevals, cancels)

    truevals_after_1 = [
        predictoor_contract.contract_instance.functions.trueValues(i).call()
        for i in epochs1
    ]

    truevals_after_2 = [
        predictoor_contract2.contract_instance.functions.trueValues(i).call()
        for i in epochs1
    ]

    for trueval in truevals_after_1:
        assert trueval == True

    for trueval in truevals_after_2[:2]:  # did not include first two epochs
        assert trueval == False

    for trueval in truevals_after_2[2:]:
        assert trueval == True


def test_consume_multiple(
    predictoor_contract: PredictoorContract,
    ocean_token: Token,
    predictoor_helper: PredictoorHelper,
):
    owner = ocean_token.config.owner

    price = predictoor_contract.get_price()
    print(price)

    times = 10
    cost = times * price

    ocean_token.approve(predictoor_helper.contract_address, cost)
    balance_before = ocean_token.balanceOf(owner)

    predictoor_helper.consume_multiple(
        [predictoor_contract.contract_address], [times], ocean_token.contract_address
    )

    balance_after = ocean_token.balanceOf(owner)
    assert balance_after + cost == balance_before