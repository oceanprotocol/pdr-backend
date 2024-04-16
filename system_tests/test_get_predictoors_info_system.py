import sys

from unittest.mock import Mock, patch, MagicMock
from pdr_backend.lake.plutil import _object_list_to_df
from pdr_backend.lake.table_pdr_predictions import (
    predictions_schema,
)
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.subgraph.prediction import Prediction
from pdr_backend.lake.table import Table
from pdr_backend.cli import cli_module
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.util.web3_config import Web3Config
from pdr_backend.lake.table_pdr_predictions import _transform_timestamp_to_ms
from pdr_backend.util.time_types import UnixTimeS
from pdr_backend.util.currency_types import Wei


@patch("pdr_backend.analytics.get_predictions_info.get_predictoor_summary_stats")
@patch("pdr_backend.analytics.get_predictions_info.GQLDataFactory.get_gql_tables")
def test_get_predictoors_info_system(
    mock_get_gql_tables, get_get_predictoor_summary_stats, caplog
):
    mock_web3_pp = MagicMock(spec=Web3PP)
    mock_web3_pp.network = "sapphire-mainnet"
    mock_web3_pp.subgraph_url = (
        "http://localhost:8000/subgraphs/name/oceanprotocol/ocean-subgraph"
    )

    mock_web3_config = Mock(spec=Web3Config)
    mock_web3_config.w3 = Mock()
    mock_web3_config.w3.eth.get_balance.return_value = 100
    mock_web3_pp.web3_config = mock_web3_config
    mock_web3_pp.web3_config.owner = "0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd"
    mock_web3_pp.owner_addrs = "0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd"

    mock_token = MagicMock()
    mock_token.balanceOf.return_value = Wei(int(5e18))
    mock_token.transfer.return_value = True
    feed_addr = "0x2d8e2267779d27c2b3ed5408408ff15d9f3a3152"
    user_addr = "0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd"

    mock_predictions = [
        Prediction(
            "{feed_addr}-31232-{user_addr}",
            feed_addr,
            "BTC",
            "5m",
            True,
            100.0,
            False,
            UnixTimeS(1701532572),
            "binance",
            10.0,
            UnixTimeS(10),
            user_addr,
        )
    ]

    st_timestr = "2023-12-03"
    fin_timestr = "2024-12-05"
    ppss = mock_ppss(
        [{"predict": "binance BTC/USDT c 5m", "train_on": "binance BTC/USDT c 5m"}],
        "sapphire-mainnet",
        ".",
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    predictions_df = _object_list_to_df(mock_predictions, predictions_schema)
    predictions_df = _transform_timestamp_to_ms(predictions_df)

    get_get_predictoor_summary_stats.return_value = predictions_df
    table = Table("pdr_predictions", predictions_schema, ppss)
    table.df = predictions_df
    mock_get_gql_tables.return_value = {"pdr_predictions": table}

    with patch("pdr_backend.contract.token.Token", return_value=mock_token), patch(
        "pdr_backend.ppss.ppss.Web3PP", return_value=mock_web3_pp
    ):
        user_addr = "0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd"
        # Mock sys.argv
        sys.argv = [
            "pdr",
            "get_predictoors_info",
            "2023-12-01",
            "2023-12-31",
            "./dir",
            "ppss.yaml",
            "development",
            "--PDRS",
            user_addr,
        ]

        cli_module._do_main()

        # Verifying outputs
        assert "pdr get_predictoors_info: Begin" in caplog.text
        assert "Arguments:" in caplog.text
        assert "PPSS_FILE=ppss.yaml" in caplog.text
        assert "NETWORK=development" in caplog.text
        assert "PDRS=['0xaaaA4CB4Ff2584BaD80fF5F109034A891C3D88Dd']" in caplog.text

        # Additional assertions
        get_get_predictoor_summary_stats.call_args[0][0].equals(predictions_df)
        mock_get_gql_tables.assert_called()
