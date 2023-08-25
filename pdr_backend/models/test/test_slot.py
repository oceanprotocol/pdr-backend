from pdr_backend.models.slot import Slot
from pdr_backend.models.contract_data import ContractData

def test_slot_initialization():
    contract = ContractData(
        "Contract Name",
        "0x12345",
        "test",
        300,
        60,
        15,
        "0xowner",
        "BTC/ETH",
        "1h",
        "binance"
    )
    
    slot_number = 5
    slot = Slot(slot_number, contract)
    
    assert slot.slot == slot_number
    assert slot.contract == contract
    assert isinstance(slot.contract, ContractData)
    