from unittest.mock import Mock, patch

from enforce_typing import enforce_types
import polars as pl

from pdr_backend.lake.table_pdr_predictions import (
    _object_list_to_df,
    predictions_schema,
)
from pdr_backend.analytics.get_predictoors_info import get_predictoors_info_main
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.ppss.web3_pp import del_network_override


@enforce_types
def test_get_predictoors_info_main_mainnet(
    _sample_first_predictions, tmpdir, monkeypatch
):
    del_network_override(monkeypatch)
    ppss = mock_ppss(["binance BTC/USDT c 5m"], "sapphire-mainnet", str(tmpdir))

    predictions_df = _object_list_to_df(_sample_first_predictions, predictions_schema)

    mock_getstats = Mock(spec=pl.DataFrame)
    mock_getPolars = Mock(return_value={"pdr_predictions": predictions_df})

    PATH = "pdr_backend.analytics.get_predictoors_info"
    with patch(f"{PATH}.get_predictoor_summary_stats", mock_getstats), patch(
        f"{PATH}.GQLDataFactory.get_gql_dfs", mock_getPolars
    ):
        get_predictoors_info_main(
            ppss,
            "0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd",
            "2023-01-01",
            "2023-01-02",
        )

        assert mock_getPolars.call_count == 1
        assert mock_getstats.call_count == 1
