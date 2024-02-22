import ccxt


class MockOrder(dict):
    def __str__(self):
        return f"mocked order: {self.get('amount')} {self['pair_str']}"


class MockExchange(ccxt.Exchange):
    def create_market_buy_order(self, symbol, amount, params={}):
        return MockOrder(
            {
                "order_type": "buy",
                "amount": str(amount),
                "pair_str": amount,
            }
        )

    def create_market_sell_order(self, symbol, amount, params={}):
        return MockOrder(
            {
                "order_type": "sell",
                "position_size": str(amount),
                "pair_str": symbol,
            }
        )

    def __str__(self):
        return "mocked exchange"
