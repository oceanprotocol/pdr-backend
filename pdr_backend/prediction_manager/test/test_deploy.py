from pdr_backend.conftest_ganache import *
from pdr_backend.prediction_manager.deploy import deploy_prediction_manager_contract  # pylint: disable=wildcard-import

def test_deploy(web3_pp):
    deployed_address = deploy_prediction_manager_contract(web3_pp)
    assert deployed_address