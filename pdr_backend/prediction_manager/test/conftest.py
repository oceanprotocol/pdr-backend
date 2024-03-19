import pytest
from pdr_backend.prediction_manager.deploy import (
    deploy_prediction_manager_contract,
)
from pdr_backend.contract.pred_submitter_manager import (
    PredSubmitterManager,
)


@pytest.fixture()
def prediction_manager(web3_pp):
    contract_address = deploy_prediction_manager_contract(web3_pp)
    return PredSubmitterManager(web3_pp, contract_address)
