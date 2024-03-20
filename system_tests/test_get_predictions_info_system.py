import sys

from unittest.mock import Mock, patch, MagicMock
from pdr_backend.lake.plutil import _object_list_to_df
from pdr_backend.lake.table_pdr_predictions import (
    predictions_schema,
)
from pdr_backend.lake.table import Table
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.subgraph.prediction import Prediction
from pdr_backend.cli import cli_module
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.util.web3_config import Web3Config
from pdr_backend.lake.table_pdr_predictions import _transform_timestamp_to_ms
from pdr_backend.util.time_types import UnixTimeS
from pdr_backend.lake.test.conftest import _clean_up_persistent_data_store
from pdr_backend.lake.persistent_data_store import PersistentDataStore


@patch("pdr_backend.analytics.get_predictions_info.get_feed_summary_stats")
def test_get_predictions_info_system(mock_get_feed_summary_stats, caplog, tmpdir):
    _clean_up_persistent_data_store(tmpdir)
    _feed = "0x2d8e2267779d27C2b3eD5408408fF15D9F3a3152"
    _user = "0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd"

    mock_predictions = [
        Prediction(
            f"{_feed}-31232-{_user}",
            _feed,
            "BTC",
            "5m",
            True,
            100.0,
            False,
            UnixTimeS(1701532572),
            "binance",
            10.0,
            UnixTimeS(10),
            _user,
        )
    ]

    st_timestr = "2023-12-03"
    fin_timestr = "2024-12-05"

    data_dir = str(tmpdir)
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        data_dir,
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    predictions_df = _object_list_to_df(mock_predictions, predictions_schema)
    predictions_df = _transform_timestamp_to_ms(predictions_df)

    PersistentDataStore(ppss.lake_ss.lake_dir).insert_to_table(
        predictions_df, "pdr_predictions"
    )

    mock_get_feed_summary_stats.return_value = predictions_df

    mock_web3_pp = MagicMock(spec=Web3PP)
    mock_web3_pp.network = "sapphire-mainnet"
    mock_web3_pp.subgraph_url = (
        "http://localhost:8000/subgraphs/name/oceanprotocol/ocean-subgraph"
    )

    mock_web3_config = Mock(spec=Web3Config)
    mock_web3_config.w3 = Mock()
    mock_web3_pp.web3_config = mock_web3_config
    mock_web3_pp.owner_addrs = _user

    with patch("pdr_backend.ppss.ppss.Web3PP", return_value=mock_web3_pp):
        # Mock sys.argv
        sys.argv = [
            "pdr",
            "get_predictions_info",
            "2023-12-01",
            "2023-12-31",
            ppss.lake_ss.lake_dir,
            "ppss.yaml",
            "development",
            "--FEEDS",
            _feed,
        ]

        cli_module._do_main()

        # Verifying outputs
        assert "pdr get_predictions_info: Begin" in caplog.text
        assert "Arguments:" in caplog.text
        assert "PPSS_FILE=ppss.yaml" in caplog.text
        assert "NETWORK=development" in caplog.text
        assert "FEEDS=['0x2d8e2267779d27C2b3eD5408408fF15D9F3a3152']" in caplog.text

        # # Additional assertions
        mock_get_feed_summary_stats.assert_called_once()
        mock_get_feed_summary_stats.call_args[0][0].equals(predictions_df)
