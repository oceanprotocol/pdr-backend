from pdr_backend.models.contract_data import ContractData

def test_contract_data_initialization():
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

    assert contract.name == "Contract Name"
    assert contract.address == "0x12345"
    assert contract.symbol == "test"
    assert contract.seconds_per_epoch == 300
    assert contract.seconds_per_subscription == 60
    assert contract.trueval_submit_timeout == 15
    assert contract.owner == "0xowner"
    assert contract.pair == "BTC/ETH"
    assert contract.timeframe == "1h"
    assert contract.source == "binance"