from pdr_backend.conftest_ganache import * # pylint: disable=wildcard-import
from pdr_backend.contract.prediction_manager import (
    PredictionManager,
)
from pdr_backend.prediction_manager.deploy import (
    deploy_prediction_manager_contract,
)


# pylint: disable=redefined-outer-name
def test_deploy(web3_pp):
    deployed_address = deploy_prediction_manager_contract(web3_pp)
    assert deployed_address

    contract = PredictionManager(web3_pp, deployed_address)
    assert contract.version()
