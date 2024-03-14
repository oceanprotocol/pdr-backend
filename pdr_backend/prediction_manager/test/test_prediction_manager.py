from pdr_backend.conftest_ganache import *
from pdr_backend.contract.prediction_manager import PredictionManager  # pylint: disable=wildcard-import
from pdr_backend.prediction_manager.deploy import (
    deploy_prediction_manager_contract,
)

def test_approve(prediction_manager: PredictionManager, predictoor_contract, predictoor_contract2, ocean_token):
    assert ocean_token.allowance(prediction_manager.contract_address, predictoor_contract.contract_address) == 0
    assert ocean_token.allowance(prediction_manager.contract_address, predictoor_contract2.contract_address) == 0
    
    contract_addrs = [predictoor_contract.contract_address, predictoor_contract2.contract_address]
    prediction_manager.approve_ocean(contract_addrs, True)
    
    assert ocean_token.allowance(prediction_manager.contract_address, predictoor_contract.contract_address) == 2**256 - 1
    assert ocean_token.allowance(prediction_manager.contract_address, predictoor_contract2.contract_address) == 2**256 - 1

@pytest.fixture(scope="module")
def prediction_manager(web3_pp):
    return deploy_prediction_manager_contract(web3_pp)