from enforce_typing import enforce_types

from pdr_backend.contract.dfrewards import DFRewards
from pdr_backend.util.contract import get_address


@enforce_types
def test_dfrewards(web3_pp, web3_config):
    dfrewards_addr = get_address(web3_pp, "DFRewards")
    assert isinstance(dfrewards_addr, str)

    ocean_addr = get_address(web3_pp, "Ocean")
    assert isinstance(dfrewards_addr, str)

    contract = DFRewards(web3_pp, dfrewards_addr)
    rewards = contract.get_claimable_rewards(web3_config.owner, ocean_addr)
    assert rewards == 0

    contract.claim_rewards(web3_config.owner, ocean_addr)
