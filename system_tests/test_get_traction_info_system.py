import sys

from unittest.mock import Mock, patch, MagicMock

from pdr_backend.cli import cli_module
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.subgraph.prediction import Prediction
from pdr_backend.subgraph.subgraph_predictions import FilterMode
from pdr_backend.util.web3_config import Web3Config


@patch("pdr_backend.analytics.get_traction_info.plot_slot_daily_statistics")
@patch("pdr_backend.lake.gql_data_factory.get_all_contract_ids_by_owner")
def test_topup(
    mock_get_all_contract_ids_by_owner,
    mock_plot_slot_daily_statistics,
):
    mock_get_all_contract_ids_by_owner.return_value = ["0xfeed"]

    mock_web3_pp = MagicMock(spec=Web3PP)
    mock_web3_pp.network = "sapphire-mainnet"
    mock_web3_pp.owner_addrs = "0xowner"
    mock_web3_pp.subgraph_url = (
        "http://localhost:8000/subgraphs/name/oceanprotocol/ocean-subgraph"
    )

    mock_web3_config = Mock(spec=Web3Config)
    mock_web3_config.w3 = Mock()
    mock_web3_config.w3.owner_address = "0xowner"
    mock_web3_pp.web3_config = mock_web3_config

    with patch(
        "pdr_backend.ppss.ppss.Web3PP", return_value=mock_web3_pp
    ):
        # Mock sys.argv
        sys.argv = [
            "pdr",
            "get_traction_info",
            "2023-12-01",
            "2023-12-31",
            "./dir",
            "ppss.yaml",
            "development",
        ]

        with patch("builtins.print") as mock_print:
            cli_module._do_main()

        # Verifying outputs
        mock_print.assert_any_call("dftool get_traction_info: Begin")
        mock_print.assert_any_call("Arguments:")
        mock_print.assert_any_call("PPSS_FILE=ppss.yaml")
        mock_print.assert_any_call("NETWORK=development")
        mock_print.assert_any_call("Get predictions data across many feeds and timeframes.")
        mock_print.assert_any_call("  Data start: timestamp=1701388800000, dt=2023-12-01_00:00:00.000")
        mock_print.assert_any_call("  Data fin: timestamp=1703980800000, dt=2023-12-31_00:00:00.000")
        mock_print.assert_any_call("Chart created:", "./dir/plots/daily_unique_predictoors.png")


        # Additional assertions
        mock_get_all_contract_ids_by_owner.assert_called()
        mock_plot_slot_daily_statistics.assert_called()
