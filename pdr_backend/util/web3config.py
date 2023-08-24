
class Web3Config:
    def __init__(self, rpc_url: str, private_key: str):
        self.rpc_url = rpc_url

        if rpc_url is None:
            raise ValueError("You must set RPC_URL variable")

        self.w3 = Web3(Web3.HTTPProvider(rpc_url))

        if private_key is not None:
            if not private_key.startswith("0x"):
                raise ValueError("Private key must start with 0x hex prefix")
            self.account: LocalAccount = Account.from_key(private_key)
            self.owner = self.account.address
            self.private_key = private_key
            self.w3.middleware_onion.add(
                construct_sign_and_send_raw_middleware(self.account)
            )


