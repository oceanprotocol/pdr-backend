import pytest
from pdr_backend.pred_submitter.deploy import (
    deploy_pred_submitter_mgr_contract,
)
from pdr_backend.contract.pred_submitter_manager import (
    PredSubmitterManager,
)


@pytest.fixture()
def pred_submitter_mgr(web3_pp):
    contract_address = deploy_pred_submitter_mgr_contract(web3_pp)
    return PredSubmitterManager(web3_pp, contract_address)
