from datetime import datetime
from os import getenv
from typing import List, Optional, Tuple

import ccxt
from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import PPSS
from pdr_backend.models.feed import SubgraphFeed
from pdr_backend.trader.approach2.portfolio import (
    Portfolio,
    Order,
    create_order,
)
from pdr_backend.trader.base_trader_agent import BaseTraderAgent


@enforce_types
class TraderAgent2(BaseTraderAgent):
    """
    @description
        Trader agent that's slightly less naive than agent 1.
    """

    def __init__(self, ppss: PPSS):
        # Initialize cache params. Must be *before* calling parent constructor!
        self.portfolio = None
        self.reset_cache = False

        #
        super().__init__(ppss)

        # If cache params are empty, instantiate
        if self.portfolio is None:
            self.portfolio = Portfolio(list(self.feeds.keys()))

        # Generic exchange clss
        exchange_class = getattr(ccxt, self.ppss.data_pp.exchange_str)
        self.exchange: ccxt.Exchange = exchange_class(
            {
                "apiKey": getenv("EXCHANGE_API_KEY"),
                "secret": getenv("EXCHANGE_SECRET_KEY"),
                "timeout": 30000,
                "options": {
                    # We're going to enable spot market purchases w/ default price
                    # Disable safety w/ createMarketBuyOrderRequiresPrice
                    "createMarketBuyOrderRequiresPrice": False,
                    "defaultType": "spot",
                },
            }
        )

        self.update_positions(list(self.feeds.keys()))

    def update_cache(self):
        super().update_cache()
        self.cache.save(f"portfolio_{self.__class__}", self.portfolio)

    def load_cache(self):
        if self.reset_cache:
            return

        super().load_cache()
        portfolio = self.cache.load(f"portfolio_{self.__class__}")
        if portfolio is not None:
            self.portfolio = portfolio

    def should_close(self, order: Order):
        """
        @description
            Check if order has lapsed in time relative to data_pp.timeframe
        """
        now_ts = int(datetime.now().timestamp() * 1000)
        tx_ts = int(order.timestamp)
        order_lapsed = now_ts - tx_ts > self.ppss.data_pp.timeframe_ms
        return order_lapsed

    def update_positions(self, feeds: Optional[List[str]] = None):
        """
        @description
            Cycle through open positions and asses them
        """
        feeds = list(self.feeds.keys()) if feeds is None or feeds == [] else feeds
        if not feeds:
            return
        if not self.portfolio:
            return

        for addr in feeds:
            sheet = self.portfolio.get_sheet(addr)
            if not sheet:
                continue

            open_positions = sheet.open_positions
            if not open_positions:
                continue

            for position in open_positions:
                should_close = self.should_close(position.open_order)
                if not should_close:
                    continue

                print("     [Close Position] Requirements met")
                order = self.exchange.create_market_sell_order(
                    self.ppss.data_pp.exchange_str,
                    position.open_order.amount,
                )
                self.portfolio.close_position(addr, order)
                self.update_cache()

    async def do_trade(self, feed: SubgraphFeed, prediction: Tuple[float, float]):
        """
        @description
            Logic:
            1. We're only going to buy. We'll always sell in 5m.
            2. Condition(If prediction == long and confidence > min)

            Step-by-step:
            1. In epoch 1, if Condition is true, we buy.
            2. In epoch 2, we sell.
            3. In epoch 2, if Condition is true, we buy.
        """

        ### First, update existing orders
        self.update_positions([feed.address])

        ### Then, create new order if our criteria is met
        pred_nom, pred_denom = prediction
        print(f"      {feed.address} has a new prediction: {pred_nom} / {pred_denom}.")

        if pred_denom == 0:
            print("  There's no stake on this, one way or the other. Exiting.")
            return

        pred_properties = self.get_pred_properties(pred_nom, pred_denom)
        print(f"      prediction properties are: {pred_properties}")

        if pred_properties["dir"] == 1 and pred_properties["confidence"] > 0.5:
            print("     [Open Position] Requirements met")
            order = self.exchange.create_market_buy_order(
                symbol=self.ppss.data_pp.exchange_str,
                amount=self.ppss.trader_ss.position_size,
            )
            if order and self.portfolio:
                order = create_order(order, self.ppss.data_pp.exchange_str)
                self.portfolio.open_position(feed.address, order)
                self.update_cache()
        else:
            print(
                f"     [No Trade] prediction does not meet requirements: {pred_properties}"
            )
