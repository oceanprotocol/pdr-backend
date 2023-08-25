class ContractData:
    def __init__(
        self,
        name: str,
        address: str,
        symbol: str,
        seconds_per_epoch: int,
        seconds_per_subscription: int,
        trueval_submit_timeout: int,
        owner: str,
        pair: str,
        timeframe: str,
        source: str,
    ):
        self.name = name
        self.address = address
        self.symbol = symbol
        self.seconds_per_epoch = seconds_per_epoch
        self.seconds_per_subscription = seconds_per_subscription
        self.trueval_submit_timeout = trueval_submit_timeout
        self.owner = owner
        self.pair = pair
        self.timeframe = timeframe
        self.source = source

    @property
    def quote(self):
        return self.pair.split("/")[1]

    @property
    def base(self):
        return self.pair.split("/")[0]
