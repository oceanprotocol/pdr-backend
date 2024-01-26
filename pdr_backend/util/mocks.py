import ccxt


class MockOrder(dict):
    def __str__(self):
        return f"mocked order: {self.get('amount')} {self['pair_str']}"


class MockExchange(ccxt.Exchange):
    def create_market_buy_order(self, pair_str, amount):
        return MockOrder(
            {
                "order_type": "buy",
                "amount": str(amount),
                "pair_str": pair_str,
            }
        )

    def create_market_sell_order(self, pair_str, position_size):
        return MockOrder(
            {
                "order_type": "sell",
                "position_size": str(position_size),
                "pair_str": pair_str,
            }
        )

    def __str__(self):
        return "mocked exchange"

