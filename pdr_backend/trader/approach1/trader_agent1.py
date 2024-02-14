import logging
from typing import Any, Dict, Optional, Tuple, Union

import ccxt
from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import PPSS
from pdr_backend.subgraph.subgraph_feed import SubgraphFeed
from pdr_backend.trader.base_trader_agent import BaseTraderAgent, Prediction

logger = logging.getLogger(__name__)


@enforce_types
class TraderAgent1(BaseTraderAgent):
    """
    @description
        Naive trader agent.
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

        # Generic exchange class
        self.exchange: ccxt.Exchange = self.ppss.trader_ss.ccxt_exchange()

        # Market and order data
        self.order: Optional[Dict[str, Any]] = None
        assert self.exchange is not None, "Exchange cannot be None"

    async def do_trade(self, feed: SubgraphFeed, prediction: Union[Prediction, Tuple]):
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
            if self.ppss.trader_ss.exchange_str == "mexc":
                amount = float(self.order["info"]["origQty"])

            # close it
            order = self.exchange.create_market_sell_order(
                self.ppss.trader_ss.pair_str, amount
            )

            logger.info("[Trade Closed] %s", self.exchange)
            logger.info("[Previous Order] %s", self.order)
            logger.info("[Closing Order] %s", order)

            self.order = None

        ### Create new order if prediction meets our criteria
        if not isinstance(prediction, Prediction):
            prediction = Prediction(prediction)

        logger.info(
            "%s has a new prediction: %s / %s.",
            feed,
            prediction.pred_nom,
            prediction.pred_denom,
        )

        if prediction.pred_denom == 0:
            logger.warning("There's no stake on this, one way or the other. Exiting.")
            return

        logger.info("prediction properties are: %s", prediction.properties)

        if prediction.direction == 1 and prediction.confidence > 0.5:
            order = self.exchange.create_market_buy_order(
                self.ppss.trader_ss.pair_str, self.ppss.trader_ss.position_size
            )

            # If order is successful, we log the order so we can close it
            if order is not None and isinstance(order, dict):
                self.order = order
                logger.info("[Trade Opened] %s", self.exchange)
                logger.info("[Opening Order] %s", order)
        else:
            logger.info(
                "[No Trade] prediction does not meet requirements: %s",
                prediction.properties,
            )
