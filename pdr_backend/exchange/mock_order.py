class MockOrder(dict):
    def __str__(self):
        return f"mocked order: {self.get('amount')} {self['pair_str']}"
