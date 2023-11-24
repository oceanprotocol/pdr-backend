from pdr_backend.ppss.publisher_ss import PublisherSS


def test_publisher_ss():
    d = {
        "sapphire-mainnet": {"fee_collector_address": "0x1"},
        "sapphire-testnet": {"fee_collector_address": "0x2"},
    }
    ss1 = PublisherSS("sapphire-mainnet", d)
    assert ss1.fee_collector_address == "0x1"

    ss2 = PublisherSS("sapphire-testnet", d)
    assert ss2.fee_collector_address == "0x2"
