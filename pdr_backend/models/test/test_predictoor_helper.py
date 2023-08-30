from pdr_backend.conftest_ganache import SECONDS_PER_EPOCH
from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.models.predictoor_helper import PredictoorHelper
from pdr_backend.util.contract import get_address
from pdr_backend.util.web3_config import Web3Config


def test_submit_truevals(
    predictoor_contract: PredictoorContract, web3_config: Web3Config, chain_id: int
):
    current_epoch = predictoor_contract.get_current_epoch_ts()

    # fast forward time
    predictoor_contract.config.w3.provider.make_request(
        "evm_increaseTime", [SECONDS_PER_EPOCH * 10]
    )
    predictoor_contract.config.w3.provider.make_request("evm_mine", [])

    end_epoch = current_epoch + SECONDS_PER_EPOCH * 10

    predictoor_helper_addr = get_address(chain_id, "PredictoorHelper")
    predictoor_helper = PredictoorHelper(web3_config, predictoor_helper_addr)

    # get trueval for epochs
    epochs = [i for i in range(current_epoch, end_epoch, SECONDS_PER_EPOCH)]
    truevals = [True] * len(epochs)
    cancels = [False] * len(epochs)
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


def test_submit_truevals_contracts():
    pass


def test_consume_multiple():
    pass
