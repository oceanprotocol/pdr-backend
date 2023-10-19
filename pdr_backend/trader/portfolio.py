class Portfolio:
    def __init__(self, initial_balance: float):
        self.balance = initial_balance # USDT
        self.position = 0 # TOKEN
        self.trades = []
        self.entry_price = None

    def buy(self, price: float, amount: float):
        self.balance -= price * amount
        assert self.balance > 0
        self.position += amount
        self.entry_price = price
        self.trades.append({"action": TradeAction.BUY, "price": price, "amount": amount})

    def sell(self, price: float, amount: float):
        self.balance += price * amount
        self.position -= amount
        assert self.position > 0
        self.entry_price = None
        self.trades.append({"action": TradeAction.SELL, "price": price, "amount": amount})

    @property
    def total_value(self, current_price: float):
        return self.balance + (self.position * current_price)
