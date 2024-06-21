import logging
from enforce_typing import enforce_types
from pdr_backend.exchange.exchange_mgr import ExchangeMgr


logger = logging.getLogger("sim_trader")


# pylint: disable=too-many-instance-attributes
class SimTrader:
    def __init__(self, ppss, predict_feed):
        self.ppss = ppss

        self.position_open = ""  # long, short, ""
        self.position_size = 0  # amount of tokens in position
        self.position_worth = 0  # amount of USD in position
        self.tp = 0.0  # take profit
        self.sl = 0.0  # stop loss
        self.tp_percent = self.ppss.trader_ss.take_profit_percent
        self.sl_percent = self.ppss.trader_ss.stop_loss_percent

        mock = self.ppss.sim_ss.tradetype in ["histmock"]
        exchange_mgr = ExchangeMgr(self.ppss.exchange_mgr_ss)
        self.exchange = exchange_mgr.exchange(
            "mock" if mock else ppss.predictoor_ss.exchange_str,
        )

        self.predict_feed = predict_feed
        assert isinstance(self.tokcoin, str)
        assert isinstance(self.usdcoin, str)

    @property
    def tokcoin(self) -> str:
        """Return e.g. 'ETH'"""
        return self.predict_feed.pair.base_str

    @property
    def usdcoin(self) -> str:
        """Return e.g. 'USDT'"""
        return self.predict_feed.pair.quote_str

    def close_long_position(self, sell_price: float) -> float:
        tokcoin_amt_send = self.position_size
        usd_received = self._sell(sell_price, tokcoin_amt_send)
        self.position_open = ""
        profit = usd_received - self.position_worth
        return profit

    def close_short_position(self, buy_price: float) -> float:
        usdcoin_amt_send = self.position_size * buy_price
        self._buy(buy_price, usdcoin_amt_send)
        self.position_open = ""
        profit = self.position_worth - usdcoin_amt_send
        return profit

    # pylint: disable = too-many-return-statements
    def trade_iter(
        self,
        cur_close: float,
        pred_up,
        pred_down,
        conf_up: float,
        conf_down: float,
        high: float,
        low: float,
    ) -> float:
        """
        @description
            Simulate trader's actions based on predictions and confidence levels.
            If trader has an open position, it will close it if the prediction
            changes. If trader has no open position, it will open a position if
            the prediction is strong enough. Also, close the position if the price
            hits the stop loss or take profit levels.

        @arguments
            cur_close -- current price of the token
            pred_up -- prediction that the price will go up
            pred_down -- prediction that the price will go down
            conf_up -- confidence in the prediction that the price will go up
            conf_down -- confidence in the prediction that the price will go down
            high -- highest price reached during the period
            low -- lowest price reached during the period


        @return
            profit -- profit made by the trader in this iteration
        """
        trade_amt = self.ppss.trader_ss.buy_amt_usd.amt_eth
        if self.position_open == "":
            if pred_up:
                # Open long position if pred up and no position open
                usdcoin_amt_send = trade_amt * (1 + conf_up)
                tok_received = self._buy(cur_close, usdcoin_amt_send)
                self.position_open = "long"
                self.position_worth = usdcoin_amt_send
                self.position_size = tok_received
                self.tp = cur_close + (cur_close * self.tp_percent)
                self.sl = cur_close - (cur_close * self.sl_percent)

            elif pred_down:
                # Open short position if pred down and no position open
                tokcoin_amt_send = trade_amt * (1 + conf_down) / cur_close
                usd_received = self._sell(cur_close, tokcoin_amt_send)
                self.position_open = "short"
                self.position_worth = usd_received
                self.position_size = tokcoin_amt_send
                self.tp = cur_close - (cur_close * self.tp_percent)
                self.sl = cur_close + (cur_close * self.sl_percent)
            return 0

        # Check for take profit or stop loss
        if self.position_open == "long":
            if high >= self.tp:
                return self.close_long_position(self.tp)

            if low <= self.sl:
                return self.close_long_position(self.sl)

            if not pred_up:
                return self.close_long_position(cur_close)

        if self.position_open == "short":
            if low <= self.tp:
                return self.close_short_position(self.tp)

            if high >= self.sl:
                return self.close_short_position(self.sl)

            if not pred_down:
                return self.close_short_position(cur_close)

        return 0

    @enforce_types
    def _buy(self, price: float, usdcoin_amt_send: float) -> float:
        """
        @description
          Buy tokcoin with usdcoin. That is, swap usdcoin for tokcoin.

        @arguments
          price -- amt of usdcoin per token
          usdcoin_amt_send -- # usdcoins to send. It sends less if have less
        @return
          tokcoin_amt_recd -- # tokcoins received.
        """
        p = self.ppss.trader_ss.fee_percent
        usdcoin_amt_fee = usdcoin_amt_send * p
        tokcoin_amt_recd = (usdcoin_amt_send - usdcoin_amt_fee) / price

        self.exchange.create_market_buy_order(
            str(self.predict_feed.pair), tokcoin_amt_recd
        )

        logger.info(
            "TX: BUY : send %8.2f %s, receive %8.2f %s, fee = %8.4f %s",
            usdcoin_amt_send,
            self.usdcoin,
            tokcoin_amt_recd,
            self.tokcoin,
            usdcoin_amt_fee,
            self.usdcoin,
        )

        return tokcoin_amt_recd

    @enforce_types
    def _sell(self, price: float, tokcoin_amt_send: float) -> float:
        """
        @description
          Sell tokcoin for usdcoin. That is, swap tokcoin for usdcoin.

        @arguments
          price -- amt of usdcoin per token
          tokcoin_amt_send -- # tokcoins to send. It sends less if have less

        @return
          usdcoin_amt_recd -- # usdcoins received
        """
        p = self.ppss.trader_ss.fee_percent
        tok_amt_fee = tokcoin_amt_send * p
        usdcoin_amt_recd = (tokcoin_amt_send - tok_amt_fee) * price

        self.exchange.create_market_sell_order(
            str(self.predict_feed.pair), tokcoin_amt_send
        )

        usdcoin_amt_fee = tok_amt_fee * price
        logger.info(
            "TX: SELL: send %8.2f %s, receive %8.2f %s, fee = %8.4f %s",
            tokcoin_amt_send,
            self.tokcoin,
            usdcoin_amt_recd,
            self.usdcoin,
            usdcoin_amt_fee,
            self.usdcoin,
        )

        return usdcoin_amt_recd
