from pdr_backend.models.feed import Feed


class Slot:
    def __init__(self, slot_number: int, feed: Feed):
        self.slot_number = slot_number
        self.feed = feed
