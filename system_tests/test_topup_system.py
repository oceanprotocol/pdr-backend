import sys

from unittest.mock import Mock, patch, MagicMock

from pdr_backend.cli import cli_module
from pdr_backend.contract.token import NativeToken, Token
from pdr_backend.ppss.topup_ss import TopupSS
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.util.web3_config import Web3Config


def test_topup(caplog):
    mock_web3_pp = MagicMock(spec=Web3PP)
    mock_web3_pp.network = "sapphire-mainnet"
    mock_web3_pp.subgraph_url = (
        "http://localhost:8000/subgraphs/name/oceanprotocol/ocean-subgraph"
    )

    mock_web3_config = Mock(spec=Web3Config)
    mock_web3_config.w3 = Mock()
    mock_web3_pp.web3_config = mock_web3_config
    mock_web3_pp.web3_config.owner = "0xowner"

    mock_token = MagicMock(spec=Token)
    balances_arr = [int(5000 * 1e18)] + [int(5 * 1e18)] * 100
    mock_token.balanceOf.side_effect = balances_arr
    mock_token.transfer.return_value = True
    mock_token.name = "OCEAN"

    mock_token_rose = MagicMock(spec=NativeToken)
    balances_arr = [int(5000 * 1e18)] + [int(5 * 1e18)] * 100
    mock_token_rose.balanceOf.side_effect = balances_arr
    mock_token_rose.transfer.return_value = True
    mock_token_rose.name = "ROSE"

    mock_web3_pp.OCEAN_Token = mock_token
    mock_web3_pp.NativeToken = mock_token_rose

    opf_addresses = {
        "predictoor1": "0x1",
        "predictoor2": "0x2",
    }
    topup_ss = MagicMock(spec=TopupSS)
    topup_ss.all_topup_addresses.return_value = opf_addresses
    topup_ss.get_min_bal.side_effect = [20, 30, 20, 30]
    topup_ss.get_topup_bal.side_effect = [20, 30, 20, 30]

    with patch("pdr_backend.ppss.ppss.Web3PP", return_value=mock_web3_pp), patch(
        "pdr_backend.ppss.ppss.TopupSS", return_value=topup_ss
    ), patch("sys.exit"):
        # Mock sys.argv
        sys.argv = ["pdr", "topup", "ppss.yaml", "sapphire-testnet"]

        cli_module._do_main()

        addresses = opf_addresses
        # Verifying outputs
        for key, value in addresses.items():
            assert f"{key}: 5.00 OCEAN, 5.00 ROSE" in caplog.text
            if key.startswith("pred"):
                assert f"\t Transferring 20 OCEAN to {value}..." in caplog.text
                assert f"\t Transferring 30 ROSE to {value}..." in caplog.text
            if key.startswith("dfbuyer"):
                assert f"\t Transferring 250 ROSE to {value}..." in caplog.text

        # Additional assertions
        mock_token.transfer.assert_called()
        mock_token.balanceOf.assert_called()
