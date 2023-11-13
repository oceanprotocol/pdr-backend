from enforce_typing import enforce_types
from pdr_backend.models.dfrewards import DFRewards

from pdr_backend.util.contract import get_address
from pdr_backend.util.web3_config import Web3Config


@enforce_types
def test_dfrewards(web3_config: Web3Config):
    dfrewards_address = get_address(web3_config.w3.eth.chain_id, "DFRewards")
    ocean_address = get_address(web3_config.w3.eth.chain_id, "Ocean")

    contract = DFRewards(web3_config, dfrewards_address)
    rewards = contract.get_claimable_rewards(web3_config.owner, ocean_address)
    assert rewards == 0

    contract.claim_rewards(web3_config.owner, ocean_address)
