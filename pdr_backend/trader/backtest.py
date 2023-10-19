from typing import Tuple
from pdr_backend.models.feed import Feed

class HistoricalDataPoint:
    def __init__(feed: Feed, price: float, prediction: float):
        self.feed = feed
        self.price = price
        self.prediction = prediction

def fetch_historical_data(n_points: int) -> List[HistoricalDataPoint]:
    pass

def backtest():
    portfolio = Portfolio(initial_balance=1000)

    print(f"      Portfolio value before trade: {portfolio.total_value(current_price)}")

    historical_data = fetch_historical_data(100)

    for historical_data_point in historical_data:
        current_price = historical_data_point.price
        prediction = historical_data_point.prediction
        feed = historical_data_point.feed
        
        action, amount = await do_trade(feed, prediction)
        
        if action == TradeAction.BUY:
            portfolio.buy(current_price, amount)
        elif action == TradeAction.SELL:
            portfolio.sell(current_price, amount)

    print(f"      Portfolio value after trade: {portfolio.total_value(current_price)}")
