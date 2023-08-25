from pdr_backend.models.contract_data import ContractData


class Slot:
    def __init__(self, slot: int, contract: ContractData):
        self.slot = slot
        self.contract = contract
