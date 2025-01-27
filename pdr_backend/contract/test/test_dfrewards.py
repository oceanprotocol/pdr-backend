from enforce_typing import enforce_types

from pdr_backend.contract.dfrewards import DFRewards
from pdr_backend.util.currency_types import Eth


@enforce_types
def test_dfrewards(web3_pp, web3_config):
    dfrewards_addr = web3_pp.get_address("DFRewards")
    assert isinstance(dfrewards_addr, str)

    ocean_addr = web3_pp.OCEAN_address
    assert isinstance(dfrewards_addr, str)

    contract = DFRewards(web3_pp, dfrewards_addr)
    rewards = contract.get_claimable_rewards(web3_config.owner, ocean_addr)
    assert rewards == Eth(0)

    contract.claim_rewards(web3_config.owner, ocean_addr)
