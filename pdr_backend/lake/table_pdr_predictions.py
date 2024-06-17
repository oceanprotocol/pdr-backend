from collections import OrderedDict

import polars as pl
from polars import Float64, Int64, Utf8

from pdr_backend.lake.lake_mapper import LakeMapper


class PredictoorSummary(LakeMapper):
    def __init__(self):
        super().__init__()
        self.check_against_schema()

    @staticmethod
    def get_lake_schema():
        return OrderedDict(
            {
                "timeframe": Utf8,
                "pair": Utf8,
                "source": Utf8,
                "accuracy": Float64,
                "sum_stake": Float64,
                "sum_payout": Float64,
                "n_predictions": Int64,
                "user": Utf8,
            }
        )


class FeedSummary(LakeMapper):
    def __init__(self):
        super().__init__()
        self.check_against_schema()

    @staticmethod
    def get_lake_schema():
        return OrderedDict(
            {
                "timeframe": Utf8,
                "pair": Utf8,
                "source": Utf8,
                "accuracy": Float64,
                "sum_stake": Float64,
                "sum_payout": Float64,
                "n_predictions": Int64,
            }
        )


def _transform_timestamp_to_ms(df: pl.DataFrame) -> pl.DataFrame:
    df = df.with_columns(
        [
            pl.col("timestamp").mul(1000).alias("timestamp"),
        ]
    )
    return df
