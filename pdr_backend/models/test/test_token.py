
@enforce_types
def test_Token(rpc_url, private_key, chain_id):
    config = Web3Config(rpc_url, private_key)
    token_address = get_address(chain_id, "Ocean")
    token = Token(config, token_address)

    accounts = config.w3.eth.accounts
    owner_addr = config.owner
    alice = accounts[1]

    token.contract_instance.functions.mint(owner_addr, 1000000000).transact(
        {"from": owner_addr, "gasPrice": config.w3.eth.gas_price}
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

