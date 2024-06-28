#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from pdr_backend.subgraph.subgraph_feed import SubgraphFeed


class Slot:
    def __init__(self, slot_number: int, feed: SubgraphFeed):
        self.slot_number = slot_number
        self.feed = feed
