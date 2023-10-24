import random
from typing import Tuple

from enforce_typing import enforce_types

from pdr_backend.trader.trader_agent import TraderAgent
from pdr_backend.trader.approach1.trader_config1 import TraderConfig1

from pdr_backend.models.feed import Feed

import ccxt
from os import getenv

CAND_ORDER_TYPE = ["market", "limit", "margin"]
CAND_SIDE = ["buy", "sell"]

@enforce_types
class TraderAgent1(TraderAgent):
    """
    @description
        TraderAgent Naive CCXT
        
        This is a naive algorithm. It will simply:
        1. If open position, close it
        2. If new prediction up, open long
        3. If new prediction down, open short

        You can use the ENV_VARS to:
        1. Configure your strategy: pair, timeframe, etc..
        2. Configure your exchange: api_key + secret_key

        You can improve this by:
        1. Improving the type of method to buy/exit (i.e. limit)
        2. Improving the buy Conditional statement
        3. Enabling buying and shorting
        4. Using SL and TP
    """    
    def __init__(self, config: TraderConfig1):
        super().__init__(config, self.do_trade)
        self.config: TraderConfig1 = config

        # Generic exchange clss
        exchange_class = getattr(ccxt, self.config.exchange_id)
        self.exchange:ccxt.Exchange = exchange_class({
            'apiKey': getenv('EXCHANGE_API_KEY'),
            'secret': getenv('EXCHANGE_SECRET_KEY'),
            "timeout": 30000,
            'options': {
                # We're going to enable spot market purchases w/ default price
                # Disable safety w/ createMarketBuyOrderRequiresPrice
                'createMarketBuyOrderRequiresPrice': False,
                'defaultType': 'spot'
            },
        })

        # Validate exchange and make it verbose
        # self.exchange.check_required_credentials() 
        
        # Let's get all the markets loaded into the cache
        # self.exchange.load_markets()

        # TODO - Add order_tracking (serializable/pickle)
        # Market and order data
        self.order = None
        self.size: float = float(getenv("POSITION_SIZE_USD")) if getenv("POSITION_SIZE_USD") else 0.0
        
        assert self.exchange != None
        assert self.size != None and self.size > 0.0
        
        # Naive parameters
        # Update from hard coded to configurable
        self.order_type = "market"
        self.side = "buy"

        assert self.order_type in CAND_ORDER_TYPE
        assert self.side in CAND_SIDE

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
        if self.order != None :
            # To sell, we need to call reduceOnly.
            order = self.exchange.create_market_sell_order(
                self.config.exchange_pair,
                self.size
            )

            print(f"     [Trade Closed] {self.exchange}")
            print(f"     [Previous Order] {self.order}")
            print(f"     [Closing Order] {order}")
            
            # TODO - Calculate PNL (self.order - order)
            self.order = None

        ### Create new order if prediction meets our criteria
        pred_nom, pred_denom = prediction
        print(f"      {feed} has a new prediction: {pred_nom} / {pred_denom}.")
        
        pred_properties  = self.get_pred_properties(pred_nom, pred_denom)
        print(f"      prediction properties are: {pred_properties}")

        if pred_properties['dir'] == 1 and pred_properties['confidence'] > 0.5 :
            order = self.exchange.create_market_buy_order(
                self.config.exchange_pair,
                self.size
            )
            
            # If order is successful, we log the order so we can close it
            if order :
                self.order = order
                print(f"     [Trade Opened] {self.exchange}")
                print(f"     [Opening Order] {order}")
        else:
            print(f"     [No Trade] prediction does not meet requirements: {pred_properties}")
                
