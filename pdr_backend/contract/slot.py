from pdr_backend.subgraph.subgraph_feed import SubgraphFeed


class Slot:
    def __init__(self, slot_number: int, feed: SubgraphFeed):
        self.slot_number = slot_number
        self.feed = feed
