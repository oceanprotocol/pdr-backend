from typing import Literal, Dict
import polars as pl

from pdr_backend.lake.plutil import (

    left_join_with,
    filter_and_drop_columns,
    pick_df_and_ids_on_period
)

Tables = Literal["payouts", "trueval", "predictins"]
FetchProcessTypes = Literal["payout", "trueval"]

class ETL:
    def __init__(self, source, destination):
        self.source = source
        self.destination = destination

        self.pdr_prediction_columns = [
            "ID",
            "truevalue_id",
            "contract",
            "pair",
            "timeframe",
            "prediction",
            "stake",
            "truevalue",
            "timestamp",
            "source",
            "payout",
            "slot",
            "user",
        ]

        self.table_data = {
            "payouts": {
                "source": "pdr_payouts.parquet",
                "data": None,
            },
            "trueval": {
                "source": "pdr_truevalue.parquet",
                "data": None,
            },
            "predictions": {
                "source": "pdr_predictions.parquet",
                "data": None,
            },
        }

    def read(
        self,
        table: Tables,
        force: bool = False,
    ) -> pl.DataFrame:
        """
        Read data from the source
        """
        if self.table_data[table]["data"] is None or force:
            self.table_data[table]["data"] = pl.read_parquet(
                f"{self.source}/{self.table_data[table]['source']}"
            )

        return self.table_data[table]["data"]

    def post_fetch_processing(
            self,
            fp_type: FetchProcessTypes,
            st_ut: int,
            fin_ut: int,
            dfs: Dict[str, pl.DataFrame]
        ):
        """
        Perform post-fetch processing on the data
        """
        if fp_type == "payout":
            self._post_fetch_processing_payout(
                st_ut, fin_ut, dfs
            )
        elif fp_type == "trueval":
            self._post_fetch_processing_trueval(
                st_ut, fin_ut, dfs
            )
        else:
            raise ValueError("Invalid fp_type")

    def _post_fetch_processing_payout(
            self,
            st_ut,
            fin_ut,
            dfs
        ):
        """
        Perform post-fetch processing on the data
        """
        payouts_df, payouts_ids = pick_df_and_ids_on_period(
            target=dfs["pdr_payouts"],
            start_timestamp=st_ut,
            finish_timestamp=fin_ut,
        )

        predictions_df = filter_and_drop_columns(
            df=dfs["pdr_predictions"],
            target_column="ID",
            ids=payouts_ids,
            columns_to_drop=["payout", "prediction"],
        )

        predictions_df = left_join_with(
            target=predictions_df,
            other=payouts_df,
            w_columns=[
                pl.col("predvalue").alias("prediction"),
            ],
            select_columns=self.pdr_prediction_columns,
        )

        predictions_df.write_parquet("pdr_predictions.parquet")


    def _post_fetch_processing_trueval(
            self,
            st_ut: int,
            fin_ut: int,
            dfs: Dict[str, pl.DataFrame]
        ):
        """
        Perform post-fetch processing on the data
        """
        truevals_df, truevals_ids = pick_df_and_ids_on_period(
            target=dfs["pdr_truevals"],
            start_timestamp=st_ut,
            finish_timestamp=fin_ut,
        )

        predictions_df = filter_and_drop_columns(
            df=dfs["pdr_predictions"],
            target_column="truevalue_id",
            ids=truevals_ids,
            columns_to_drop=["truevalue"],
        )

        predictions_df = left_join_with(
            target=predictions_df,
            other=truevals_df,
            left_on="truevalue_id",
            right_on="ID",
            w_columns=[
                pl.col("truevalue").alias("truevalue"),
            ],
            select_columns=self.pdr_prediction_columns,
        )

        predictions_df.write_parquet("pdr_predictions.parquet")
    