from unittest.mock import Mock, patch

from enforce_typing import enforce_types
import polars as pl

from pdr_backend.lake.table_pdr_predictions import (
    _object_list_to_df,
    predictions_schema,
)
from pdr_backend.analytics.get_predictions_info import get_predictions_info_main
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.ppss.web3_pp import del_network_override


@enforce_types
def test_get_predictions_info_main_mainnet(
    _sample_first_predictions,
    tmpdir,
    monkeypatch,
):
    del_network_override(monkeypatch)
    ppss = mock_ppss(["binance BTC/USDT c 5m"], "sapphire-mainnet", str(tmpdir))

    predictions_df = _object_list_to_df(_sample_first_predictions, predictions_schema)

    mock_getstats = Mock(spec=pl.DataFrame)
    mock_getPolars = Mock(return_value={"pdr_predictions": predictions_df})

    PATH = "pdr_backend.analytics.get_predictions_info"
    with patch(f"{PATH}.get_feed_summary_stats", mock_getstats), patch(
        f"{PATH}.GQLDataFactory.get_gql_dfs", mock_getPolars
    ):
        get_predictions_info_main(
            ppss,
            "2023-11-02",
            "2023-11-05",
            "0x18f54cc21b7a2fdd011bea06bba7801b280e3151",
        )

        assert mock_getPolars.call_count == 1
        assert mock_getstats.call_count == 1


@enforce_types
def test_get_predictions_info_empty(tmpdir, capfd):
    ppss = mock_ppss(["binance BTC/USDT c 5m"], "sapphire-mainnet", str(tmpdir))

    mock_getstats = Mock(spec=pl.DataFrame)
    mock_getPolars = Mock(return_value={"pdr_predictions": []})

    PATH = "pdr_backend.analytics.get_predictions_info"
    with patch(f"{PATH}.get_feed_summary_stats", mock_getstats), patch(
        f"{PATH}.GQLDataFactory.get_gql_dfs", mock_getPolars
    ):
        get_predictions_info_main(
            ppss,
            "2023-11-02",
            "2023-11-05",
            "0x18f54cc21b7a2fdd011bea06bba7801b280e3151",
        )

    assert (
        "No records found. Please adjust start and end times" in capfd.readouterr().out
    )
