from unittest.mock import Mock, patch

from enforce_typing import enforce_types

from pdr_backend.analytics.get_predictoors_info import get_predictoors_info_main
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.ppss.web3_pp import del_network_override
from pdr_backend.subgraph.subgraph_predictions import FilterMode


@enforce_types
def test_get_predictoors_info_main_mainnet(tmpdir, monkeypatch):
    del_network_override(monkeypatch)
    ppss = mock_ppss(["binance BTC/USDT c 5m"], "sapphire-mainnet", str(tmpdir))

    mock_fetch = Mock(return_value=[])
    mock_save = Mock()
    mock_getstats = Mock()

    PATH = "pdr_backend.analytics.get_predictoors_info"
    with patch(f"{PATH}.fetch_filtered_predictions", mock_fetch), patch(
        f"{PATH}.save_prediction_csv", mock_save
    ), patch(f"{PATH}.get_cli_statistics", mock_getstats):
        get_predictoors_info_main(
            ppss,
            "0x123",
            "2023-01-01",
            "2023-01-02",
            "parquet_data/",
        )

        mock_fetch.assert_called_with(
            1672531200,
            1672617600,
            ["0x123"],
            "mainnet",
            FilterMode.PREDICTOOR,
        )
        mock_save.assert_called_with([], "parquet_data/")
        mock_getstats.assert_called_with([])
