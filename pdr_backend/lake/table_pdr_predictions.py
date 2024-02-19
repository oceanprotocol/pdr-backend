import polars as pl
from polars import Boolean, Float64, Int64, Utf8

predictions_table_name = "pdr_predictions"

# RAW PREDICTOOR PREDICTIONS SCHEMA
predictions_schema = {
    "ID": Utf8,
    "pair": Utf8,
    "timeframe": Utf8,
    "prediction": Boolean,
    "stake": Float64,
    "trueval": Boolean,
    "timestamp": Int64,
    "source": Utf8,
    "payout": Float64,
    "slot": Int64,
    "user": Utf8,
}

# PREDICTOOR_SUMMARY_SCHEMA
predictoor_summary_df_schema = {
    "timeframe": Utf8,
    "pair": Utf8,
    "source": Utf8,
    "accuracy": Float64,
    "sum_stake": Float64,
    "sum_payout": Float64,
    "n_predictions": Int64,
    "user": Utf8,
}

# FEED_SUMMARY_SCHEMA
feed_summary_df_schema = {
    "timeframe": Utf8,
    "pair": Utf8,
    "source": Utf8,
    "accuracy": Float64,
    "sum_stake": Float64,
    "sum_payout": Float64,
    "n_predictions": Int64,
}


def _transform_timestamp_to_ms(df: pl.DataFrame) -> pl.DataFrame:
    df = df.with_columns(
        [
            pl.col("timestamp").mul(1000).alias("timestamp"),
        ]
    )
    return df
