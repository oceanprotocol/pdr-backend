
from pdr_backend.utils.contract import (
    is_sapphire_network,
    send_encrypted_tx,
    Web3Config,
    Token,
    PredictoorContract,
    FixedRate,
    get_contract_filename,
    )
from pdr_backend.utils.constants import (
    SAPPHIRE_TESTNET_CHAINID,
    SAPPHIRE_MAINNET_CHAINID,
)

def test_is_sapphire_network():
    assert not is_sapphire_network(0)
    assert is_sapphire_network(SAPPHIRE_TESTNET_CHAINID)
    assert is_sapphire_network(SAPPHIRE_MAINNET_CHAINID)

