from os import getenv
from typing import Any, Dict, Tuple, Optional

import ccxt
from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import PPSS
from pdr_backend.models.feed import Feed
from pdr_backend.trader.trader_agent import TraderAgent


@enforce_types
class TraderAgent1(TraderAgent):
    """
    @description
        TraderAgent Naive CCXT
        - Market order buy-only
        - Doesn't save client state or manage pending open trades
        - Only works with MEXC. How to improve:
            (A) Use Agent2/Order class to add more exchanges
            (B) Use ccxt.exchange lib to dynamically populate balances/trades/positions/etc...
        - In MEXC: You can trade BTC/USDC or WBTC/USDT, but not BTC/USDT.

        Naive long-only strategy.
        1. If existing open position, close it.
        2. If new long prediction meets criteria, open long.

        You can improve this by:
        1. Improving how to enter/exit trade w/ orders
        2. Improving when to buy
        3. Enabling buying and shorting
        4. Using SL and TP
    """

    def __init__(self, ppss: PPSS):
        super().__init__(ppss)

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

        # Market and order data
        self.order: Optional[Dict[str, Any]] = None
        assert self.exchange is not None, "Exchange cannot be None"

    async def do_trade(self, feed: Feed, prediction: Tuple[float, float]):
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

        ### Close previous order if it exists
        if self.order is not None and isinstance(self.order, dict):
            # get existing long position
            amount = 0.0
            if self.ppss.data_pp.exchange_str == "mexc":
                amount = float(self.order["info"]["origQty"])

            # close it
            order = self.exchange.create_market_sell_order(
                self.ppss.data_pp.pair_str, amount
            )

            print(f"     [Trade Closed] {self.exchange}")
            print(f"     [Previous Order] {self.order}")
            print(f"     [Closing Order] {order}")

            # TO DO - Calculate PNL (self.order - order)
            self.order = None

        ### Create new order if prediction meets our criteria
        pred_nom, pred_denom = prediction
        print(f"      {feed} has a new prediction: {pred_nom} / {pred_denom}.")

        if pred_denom == 0:
            print("  There's no stake on this, one way or the other. Exiting.")
            return

        pred_properties = self.get_pred_properties(pred_nom, pred_denom)
        print(f"      prediction properties are: {pred_properties}")

        if pred_properties["dir"] == 1 and pred_properties["confidence"] > 0.5:
            order = self.exchange.create_market_buy_order(
                self.ppss.data_pp.pair_str, self.ppss.trader_ss.position_size
            )

            # If order is successful, we log the order so we can close it
            if order is not None and isinstance(order, dict):
                self.order = order
                print(f"     [Trade Opened] {self.exchange}")
                print(f"     [Opening Order] {order}")
        else:
            print(
                f"     [No Trade] prediction does not meet requirements: {pred_properties}"
            )
