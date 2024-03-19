from pdr_backend.conftest_ganache import *  # pylint: disable=wildcard-import
from pdr_backend.contract.pred_submitter_manager import (
    PredSubmitterMgr,
)
from pdr_backend.pred_submitter.deploy import (
    deploy_pred_submitter_mgr_contract,
)


# pylint: disable=redefined-outer-name
def test_deploy(web3_pp):
    deployed_address = deploy_pred_submitter_mgr_contract(web3_pp)
    assert deployed_address

    contract = PredSubmitterMgr(web3_pp, deployed_address)
    assert contract.version()
