from io import StringIO
import os
import sys
from polars import Boolean, Float64, Int64, Utf8
import polars as pl
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.lake.table import Table

mocked_object = {
    "ID": "0x123",
    "pair": "ADA-USDT",
    "timeframe": "5m",
    "prediction": True,
    "payout": 28.2,
    "timestamp": 1701634400000,
    "slot": 1701634400000,
    "user": "0x123",
}


def get_table_df(network, st_ut, fin_ut, config):
    print(network, st_ut, fin_ut, config)
    return pl.DataFrame([mocked_object], table_df_schema)


table_df_schema = {
    "ID": Utf8,
    "pair": Utf8,
    "timeframe": Utf8,
    "prediction": Boolean,
    "payout": Float64,
    "timestamp": Int64,
    "slot": Int64,
    "user": Utf8,
}
table_name = "pdr_test_df"
file_path = f"./parquet_data/{table_name}.parquet"


def test_table_initialization(tmpdir):
    st_timestr = "2023-12-03"
    fin_timestr = "2024-12-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )
    print(ppss)

    table = Table(table_name, table_df_schema, get_table_df, ppss)
    assert len(table.df) == 0
    assert table.df.columns == table.df.columns
    assert table.df.dtypes == table.df.dtypes
    assert table.table_name == table_name
    assert table.ppss.lake_ss.st_timestr == st_timestr
    assert table.ppss.lake_ss.fin_timestr == fin_timestr
    assert callable(table.build)


def test_load_table():
    st_timestr = "2023-12-03"
    fin_timestr = "2024-12-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        ".",
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    table = Table(table_name, table_df_schema, get_table_df, ppss)
    table.load()


# assert len(table.df > 0)


def test_update_table():
    st_timestr = "2023-12-03"
    fin_timestr = "2024-12-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        ".",
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    config = {
        "contract_list": ["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"],
    }
    table = Table(table_name, table_df_schema, get_table_df, ppss)

    assert len(table.df) == 0
    table.update(config)
    assert len(table.df) == 1


def test_save_table():
    st_timestr = "2023-12-03"
    fin_timestr = "2023-12-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        ".",
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    table = Table(table_name, table_df_schema, get_table_df, ppss)

    captured_output = StringIO()
    sys.stdout = captured_output

    assert len(table.df) == 0
    table.df = pl.DataFrame([mocked_object], table_df_schema)
    table.save()

    assert os.path.exists(file_path)
    printed_text = captured_output.getvalue().strip()
    if os.path.exists(file_path):
        assert "  Just appended" in printed_text
    else:
        assert "  Just saved df with" in printed_text


def test_all():
    st_timestr = "2023-12-03"
    fin_timestr = "2023-12-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        ".",
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    table = Table(table_name, table_df_schema, get_table_df, ppss)

    captured_output = StringIO()
    sys.stdout = captured_output

    assert len(table.df) == 0
    config = {
        "contract_list": ["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"],
    }
    table.update(config)
    table.load()

    assert len(table.df) == 1


'''
@patch("pdr_backend.lake.table_pdr_predictions.fetch_filtered_predictions")
@patch("pdr_backend.lake.gql_data_factory.get_all_contract_ids_by_owner")
def test_update_gql1(
    mock_get_all_contract_ids_by_owner,
    mock_fetch_filtered_predictions,
    tmpdir,
    sample_daily_predictions,
):
    mock_get_all_contract_ids_by_owner.return_value = ["0x123"]
    _test_update_gql(
        mock_fetch_filtered_predictions,
        tmpdir,
        sample_daily_predictions,
        "2023-11-02_0:00",
        "2023-11-04_21:00",
        n_preds=3,
    )

@patch("pdr_backend.lake.table_pdr_predictions.fetch_filtered_predictions")
@patch("pdr_backend.lake.gql_data_factory.get_all_contract_ids_by_owner")
def test_update_gql_iteratively(
    mock_get_all_contract_ids_by_owner,
    mock_fetch_filtered_predictions,
    tmpdir,
    sample_daily_predictions,
):
    mock_get_all_contract_ids_by_owner.return_value = ["0x123"]

    iterations = [
        ("2023-11-02_0:00", "2023-11-04_0:00", 2),
        ("2023-11-01_0:00", "2023-11-05_0:00", 3),  # do not append to start
        ("2023-11-02_0:00", "2023-11-07_0:00", 5),
    ]

    for st_timestr, fin_timestr, n_preds in iterations:
        _test_update_gql(
            mock_fetch_filtered_predictions,
            tmpdir,
            sample_daily_predictions,
            st_timestr,
            fin_timestr,
            n_preds=n_preds,
        )


@enforce_types
def _test_update_gql(
    mock_fetch_filtered_predictions,
    tmpdir,
    sample_predictions,
    st_timestr: str,
    fin_timestr: str,
    n_preds,
):
    """
    @arguments
      n_preds -- expected # predictions. Typically int. If '>1K', expect >1000
    """

    _, gql_data_factory = _gql_data_factory(
        tmpdir,
        "binanceus ETH/USDT h 5m",
        st_timestr,
        fin_timestr,
    )

    # Update predictions record only
    gql_data_factory.record_config = _filter_gql_config(
        gql_data_factory.record_config, pdr_predictions_record
    )

    # setup: filename
    # everything will be inside the gql folder
    filename = gql_data_factory._parquet_filename(pdr_predictions_record)
    assert ".parquet" in filename

    fin_ut = timestr_to_ut(fin_timestr)
    st_ut = gql_data_factory._calc_start_ut(filename)

    # calculate ms locally so we can filter raw Predictions
    st_ut_sec = st_ut // 1000
    fin_ut_sec = fin_ut // 1000

    # filter preds that will be returned from subgraph to client
    target_preds = [
        x for x in sample_predictions if st_ut_sec <= x.timestamp <= fin_ut_sec
    ]
    mock_fetch_filtered_predictions.return_value = target_preds

    # work 1: update parquet
    gql_data_factory._update(fin_ut)

    # assert params
    mock_fetch_filtered_predictions.assert_called_with(
        st_ut_sec,
        fin_ut_sec,
        ["0x123"],
        "mainnet",
        FilterMode.CONTRACT_TS,
        payout_only=False,
        trueval_only=False,
    )

    # read parquet and columns
    def _preds_in_parquet(filename: str) -> List[int]:
        df = pl.read_parquet(filename)
        assert df.schema == predictions_schema
        return df["timestamp"].to_list()

    # assert expected length of preds in parquet
    preds: List[int] = _preds_in_parquet(filename)
    if isinstance(n_preds, int):
        assert len(preds) == n_preds
    elif n_preds == ">1K":
        assert len(preds) > 1000

    # preds may not match start or end time
    assert preds[0] != st_ut
    assert preds[-1] != fin_ut

    # assert all target_preds are registered in parquet
    target_preds_ts = [pred.__dict__["timestamp"] for pred in target_preds]
    for target_pred in target_preds_ts:
        assert target_pred * 1000 in preds


@patch("pdr_backend.lake.table_pdr_predictions.fetch_filtered_predictions")
@patch("pdr_backend.lake.gql_data_factory.get_all_contract_ids_by_owner")
def test_load_and_verify_schema(
    mock_get_all_contract_ids_by_owner,
    mock_fetch_filtered_predictions,
    tmpdir,
    sample_daily_predictions,
):
    st_timestr = "2023-11-02_0:00"
    fin_timestr = "2023-11-07_0:00"

    mock_get_all_contract_ids_by_owner.return_value = ["0x123"]

    _test_update_gql(
        mock_fetch_filtered_predictions,
        tmpdir,
        sample_daily_predictions,
        st_timestr,
        fin_timestr,
        n_preds=5,
    )

    _, gql_data_factory = _gql_data_factory(
        tmpdir,
        "binanceus ETH/USDT h 5m",
        st_timestr,
        fin_timestr,
    )
    gql_data_factory.record_config = _filter_gql_config(
        gql_data_factory.record_config, pdr_predictions_record
    )

    tables = gql_data_factory._load_parquet()

    assert len(tables) == 1
    assert len(tables[pdr_predictions_record].df) == 5
    assert tables[pdr_predictions_record].df.schema == predictions_schema


# ====================================================================
# test if appropriate calls are made


@enforce_types
@patch("pdr_backend.lake.gql_data_factory.get_all_contract_ids_by_owner")
@patch("pdr_backend.lake.gql_data_factory.GQLDataFactory._update")
@patch("pdr_backend.lake.gql_data_factory.GQLDataFactory._load_parquet")
def test_get_gql_dfs_calls(
    mock_load_parquet,
    mock_update,
    mock_get_all_contract_ids_by_owner,
    tmpdir,
    sample_daily_predictions,
):
    """Test core DataFactory functions are being called"""

    st_timestr = "2023-11-02_0:00"
    fin_timestr = "2023-11-07_0:00"

    mock_get_all_contract_ids_by_owner.return_value = ["0x123"]

    _, gql_data_factory = _gql_data_factory(
        tmpdir,
        "binanceus ETH/USDT h 5m",
        st_timestr,
        fin_timestr,
    )

    # Update predictions record only
    default_config = gql_data_factory.record_config
    gql_data_factory.record_config = _filter_gql_config(
        gql_data_factory.record_config, pdr_predictions_record
    )

    # calculate ms locally so we can filter raw Predictions
    st_ut = timestr_to_ut(st_timestr)
    fin_ut = timestr_to_ut(fin_timestr)
    st_ut_sec = st_ut // 1000
    fin_ut_sec = fin_ut // 1000

    # mock_load_parquet should return the values from a simple code block
    mock_load_parquet.return_value = {
        pdr_predictions_record: pl.DataFrame(
            [
                x.__dict__
                for x in sample_daily_predictions
                if st_ut_sec <= x.timestamp <= fin_ut_sec
            ]
        ).with_columns([pl.col("timestamp").mul(1000).alias("timestamp")])
    }

    # call and assert
    gql_dfs = gql_data_factory.get_gql_dfs()
    assert isinstance(gql_dfs, dict)
    assert isinstance(gql_dfs[pdr_predictions_record], pl.DataFrame)
    assert len(gql_dfs[pdr_predictions_record]) == 5

    mock_update.assert_called_once()
    mock_load_parquet.assert_called_once()

    # reset record config
    gql_data_factory.record_config = default_config


# ====================================================================
# test loading flow when there are pdr files missing


@enforce_types
@patch("pdr_backend.lake.table_pdr_predictions.fetch_filtered_predictions")
@patch("pdr_backend.lake.table_pdr_subscriptions.fetch_filtered_subscriptions")
@patch("pdr_backend.lake.gql_data_factory.get_all_contract_ids_by_owner")
def test_load_missing_parquet(
    mock_get_all_contract_ids_by_owner,
    mock_fetch_filtered_subscriptions,
    mock_fetch_filtered_predictions,
    tmpdir,
    sample_daily_predictions,
):
    """Test core DataFactory functions are being called"""

    mock_get_all_contract_ids_by_owner.return_value = ["0x123"]
    mock_fetch_filtered_subscriptions.return_value = []
    mock_fetch_filtered_predictions.return_value = []

    st_timestr = "2023-11-02_0:00"
    fin_timestr = "2023-11-04_0:00"

    _, gql_data_factory = _gql_data_factory(
        tmpdir,
        "binanceus ETH/USDT h 5m",
        st_timestr,
        fin_timestr,
    )

    # Work 1: Fetch empty dataset
    # (1) perform empty fetch
    # (2) do not save to parquet
    # (3) handle missing parquet file
    # (4) assert we get empty dataframes with the expected schema
    dfs = gql_data_factory.get_gql_dfs()

    predictions_table = "pdr_predictions"
    subscriptions_table = "pdr_subscriptions"

    assert len(dfs[predictions_table]) == 0
    assert len(dfs[subscriptions_table]) == 0

    assert (
        dfs[predictions_table].schema
        == gql_data_factory.record_config[predictions_table]["schema"]
    )
    assert (
        dfs[subscriptions_table].schema
        == gql_data_factory.record_config[subscriptions_table]["schema"]
    )

    # Work 2: Fetch 1 dataset
    # (1) perform 1 successful datafactory loops (predictions)
    # (2) assert subscriptions parquet doesn't exist / has 0 records
    _test_update_gql(
        mock_fetch_filtered_predictions,
        tmpdir,
        sample_daily_predictions,
        st_timestr,
        fin_timestr,
        n_preds=2,
    )

    dfs = gql_data_factory.get_gql_dfs()
    assert len(dfs[predictions_table]) == 2
    assert len(dfs[subscriptions_table]) == 0
'''
