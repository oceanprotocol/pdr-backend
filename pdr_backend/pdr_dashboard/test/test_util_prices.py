from unittest.mock import MagicMock

from pdr_backend.pdr_dashboard.util.prices import calculate_tx_gas_fee_cost_in_OCEAN


def test_calculate_tx_gas_fee_cost_in_OCEAN():
    # Example feed_contract_addr
    feed_contract_addr = "0x1234567890abcdef1234567890abcdef12345678"

    # Example web3_pp mock
    web3_pp = MagicMock()
    web3_pp.rpc_url = "https://testnet.sapphire.oasis.dev"
    web3_pp.get_contract_abi.return_value = [
        {
            "constant": False,
            "inputs": [
                {"name": "predicted_value", "type": "bool"},
                {"name": "stake_amt_wei", "type": "uint256"},
                {"name": "prediction_ts", "type": "uint256"},
            ],
            "name": "submitPredval",
            "outputs": [],
            "payable": False,
            "stateMutability": "nonpayable",
            "type": "function",
        }
    ]

    # If no prices, should return 0
    result = calculate_tx_gas_fee_cost_in_OCEAN(web3_pp, feed_contract_addr, None)
    assert isinstance(result, float)
    assert result == 0.0

    # If prices, should return a value > 0
    result = calculate_tx_gas_fee_cost_in_OCEAN(
        web3_pp, feed_contract_addr, {"OCEAN": 0.1, "ROSE": 0.01}
    )
    assert isinstance(result, float)
    assert result > 0
    assert result < 0.001
