import time

from enforce_typing import enforce_types

from pdr_backend.util.contract import get_address
from pdr_backend.models.token import Token


@enforce_types
def test_Token(web3_config, chain_id):
    token_address = get_address(chain_id, "Ocean")
    token = Token(web3_config, token_address)

    accounts = web3_config.w3.eth.accounts
    owner_addr = web3_config.owner
    alice = accounts[1]

    token.contract_instance.functions.mint(owner_addr, 1000000000).transact(
        {"from": owner_addr, "gasPrice": web3_config.w3.eth.gas_price}
    )

    allowance_start = token.allowance(owner_addr, alice)
    token.approve(alice, allowance_start + 100, True)
    time.sleep(1)
    allowance_end = token.allowance(owner_addr, alice)
    assert allowance_end - allowance_start == 100

    balance_start = token.balanceOf(alice)
    token.transfer(alice, 100, owner_addr)
    balance_end = token.balanceOf(alice)
    assert balance_end - balance_start == 100
