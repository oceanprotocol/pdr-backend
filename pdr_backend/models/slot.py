from pdr_backend.models.feed import Feed


class Slot:
    def __init__(self, slot: int, feed: Feed):
        self.slot = slot
        self.feed = feed
