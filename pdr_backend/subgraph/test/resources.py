from enforce_typing import enforce_types


@enforce_types
class MockResponse:
    def __init__(self, contract_list: list, status_code: int):
        self.contract_list = contract_list
        self.status_code = status_code
        self.num_queries = 0

    def json(self) -> dict:
        self.num_queries += 1
        if self.num_queries > 1:
            self.contract_list = []
        return {"data": {"predictContracts": self.contract_list}}


@enforce_types
class MockPost:
    def __init__(self, contract_list: list = [], status_code: int = 200):
        self.response = MockResponse(contract_list, status_code)

    def __call__(self, *args, **kwargs):
        return self.response
