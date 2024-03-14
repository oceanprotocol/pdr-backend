from pdr_backend.conftest_ganache import *
from pdr_backend.contract.prediction_manager import (
    PredictionManager,
)  # pylint: disable=wildcard-import
from pdr_backend.prediction_manager.deploy import (
    deploy_prediction_manager_contract,
)


def test_approve(
    prediction_manager: PredictionManager,
    predictoor_contract,
    predictoor_contract2,
    ocean_token,
):
    assert (
        ocean_token.allowance(
            prediction_manager.contract_address, predictoor_contract.contract_address
        )
        == 0
    )
    assert (
        ocean_token.allowance(
            prediction_manager.contract_address, predictoor_contract2.contract_address
        )
        == 0
    )

    contract_addrs = [
        predictoor_contract.contract_address,
        predictoor_contract2.contract_address,
    ]
    prediction_manager.approve_ocean(contract_addrs, True)

    assert (
        ocean_token.allowance(
            prediction_manager.contract_address, predictoor_contract.contract_address
        )
        == 2**256 - 1
    )
    assert (
        ocean_token.allowance(
            prediction_manager.contract_address, predictoor_contract2.contract_address
        )
        == 2**256 - 1
    )


def test_transfer_erc20(
    prediction_manager: PredictionManager, ocean_token, web3_config
):
    ocean_token.transfer(prediction_manager.contract_address, 100)
    assert ocean_token.balance_of(prediction_manager.contract_address) == 100
    before = ocean_token.balance_of(web3_config.owner)
    prediction_manager.transfer_erc20(
        ocean_token.contract_address, web3_config.owner, 100
    )
    after = ocean_token.balance_of(web3_config.owner)
    assert after - before == 100
    assert ocean_token.balance_of(prediction_manager.contract_address) == 0


def test_transfer(prediction_manager: PredictionManager, web3_config):
    web3_config.w3.eth.send_transaction(
        {"to": prediction_manager.contract_address, "value": 100}
    )
    assert web3_config.w3.eth.get_balance(prediction_manager.contract_address) == 100
    before = web3_config.w3.eth.get_balance(web3_config.owner)
    prediction_manager.transfer()
    after = web3_config.w3.eth.get_balance(web3_config.owner)
    assert after - before == 100
    assert web3_config.w3.eth.get_balance(prediction_manager.contract_address) == 0


@pytest.fixture(scope="module")
def prediction_manager(web3_pp):
    return deploy_prediction_manager_contract(web3_pp)
