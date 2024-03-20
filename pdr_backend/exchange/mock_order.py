from enforce_typing import enforce_types


@enforce_types
class MockOrder(dict):
    def __str__(self):
        return f"mocked order: {self.get('amount')} {self['pair_str']}"
