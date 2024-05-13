import sys
from unittest.mock import MagicMock, Mock, patch

from pdr_backend.cli import cli_module
from pdr_backend.lake.persistent_data_store import PersistentDataStore
from pdr_backend.lake.plutil import _object_list_to_df
from pdr_backend.lake.prediction import Prediction
from pdr_backend.lake.table_pdr_predictions import _transform_timestamp_to_ms
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.util.time_types import UnixTimeS
from pdr_backend.util.web3_config import Web3Config


@patch("pdr_backend.analytics.get_predictions_info.plot_slot_daily_statistics")
def test_traction_info_system(mock_plot_stats, caplog):
    feed_addr = "0x2d8e2267779d27c2b3ed5408408ff15d9f3a3152"
    user_addr = "0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd"
    mock_predictions = [
        Prediction(
            f"{feed_addr}-31232-{user_addr}",
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

    predictions_df = _object_list_to_df(mock_predictions)
    predictions_df = _transform_timestamp_to_ms(predictions_df)

    # DROP TABLE IF EXISTS
    PersistentDataStore(ppss.lake_ss.lake_dir).drop_table("pdr_predictions")

    PersistentDataStore(ppss.lake_ss.lake_dir).insert_to_table(
        predictions_df, "pdr_predictions"
    )

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

    with patch("pdr_backend.ppss.ppss.Web3PP", return_value=mock_web3_pp):
        # Mock sys.argv
        sys.argv = [
            "pdr",
            "get_traction_info",
            "2023-12-01",
            "2023-12-31",
            ppss.lake_ss.lake_dir,
            "ppss.yaml",
            "sapphire-mainnet",
        ]

        cli_module._do_main()

        # Verifying outputs
        assert "pdr get_traction_info: Begin" in caplog.text
        assert "Arguments:" in caplog.text
        assert "PPSS_FILE=ppss.yaml" in caplog.text
        assert "NETWORK=sapphire-mainnet" in caplog.text
        assert caplog.text.count("Chart created:") == 2

        # Additional assertions
        mock_plot_stats.assert_called()
