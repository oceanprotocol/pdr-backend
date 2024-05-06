import logging

from enforce_typing import enforce_types

from pdr_backend.util.logger_base import BaseLogLine

logger = logging.getLogger("predictoor_agent")


@enforce_types
class PredictoorAgentLogLine(BaseLogLine):
    def __init__(self, ppss, target_slot, stake_tup):
        self.ppss = ppss
        self.feed = stake_tup.feed
        self.target_slot = target_slot
        self.stake_up = stake_tup.stake_up
        self.stake_down = stake_tup.stake_down

        # unused for now, but supports future configuration from ppss
        self.format = "compact"

    def log_line(self):
        feed_str = (
            f"{self.feed.source} "
            f"{self.feed.pair} "
            f"{self.feed.timeframe} "
            f"{self.feed.address[:6]}"
        )

        log_msg = f"Predicted feed {feed_str}, "
        log_msg += (
            f"slot: {self.target_slot}: "
            f"up = {self._compactNum('stake_up', use_eth=True)} OCEAN"
        )
        up_stake_percentage = (
            self.stake_up.amt_eth
            / (self.stake_up.amt_eth + self.stake_down.amt_eth)
            * 100
        )
        log_msg += (
            f" down = {self._compactNum('stake_down', use_eth=True)} OCEAN "
            f"({self._compactNum(up_stake_percentage)}% up)"
        )

        logger.info(log_msg)
