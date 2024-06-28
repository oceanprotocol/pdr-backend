#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging

from enforce_typing import enforce_types

from pdr_backend.util.strutil import compactSmallNum

logger = logging.getLogger("predictoor_agent")


@enforce_types
class PredictoorAgentLogLine:
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
            f"up = {compactSmallNum(self.stake_up.amt_eth)} OCEAN"
        )
        up_stake_percentage = (
            self.stake_up.amt_eth
            / (self.stake_up.amt_eth + self.stake_down.amt_eth)
            * 100
        )
        log_msg += (
            f" down = {compactSmallNum(self.stake_down.amt_eth)} OCEAN "
            f"({compactSmallNum(up_stake_percentage)}% up)"
        )

        logger.info(log_msg)
