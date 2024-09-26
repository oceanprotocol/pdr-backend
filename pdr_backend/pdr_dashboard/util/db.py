import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple, Union

import polars as pl
from enforce_typing import enforce_types

from pdr_backend.lake.duckdb_data_store import tbl_parquet_path
from pdr_backend.lake.prediction import Prediction
from pdr_backend.lake.slot import Slot
from pdr_backend.lake.subscription import Subscription
from pdr_backend.lake.table_bronze_pdr_predictions import BronzePrediction
from pdr_backend.pdr_dashboard.util.format import (
    FEEDS_HOME_PAGE_TABLE_COLS,
    FEEDS_TABLE_COLS,
    PREDICTOORS_HOME_PAGE_TABLE_COLS,
    PREDICTOORS_TABLE_COLS,
    format_df,
)
from pdr_backend.pdr_dashboard.util.prices import (
    calculate_tx_gas_fee_cost_in_OCEAN,
    fetch_token_prices,
)
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.util.constants_opf_addrs import get_opf_addresses
from pdr_backend.pdr_dashboard.util.duckdb_file_reader import DuckDBFileReader
from pdr_backend.util.time_types import UnixTimeMs, UnixTimeS

logger = logging.getLogger("dashboard_db")


# pylint: disable=too-many-instance-attributes
class AppDataManager:
    def __init__(self, ppss: PPSS):
        self.network_name = ppss.web3_pp.network
        self.start_date: Optional[datetime] = None
        self.lake_dir = ppss.lake_ss.lake_dir
        self.file_reader = DuckDBFileReader(
            ppss.lake_ss.lake_dir, ppss.lake_ss.seconds_between_parquet_exports
        )

        self.min_timestamp, self.max_timestamp = (
            self.get_first_and_last_slot_timestamp()
        )

        # fetch token prices
        self.fee_cost = calculate_tx_gas_fee_cost_in_OCEAN(
            ppss.web3_pp,
            "0x18f54cc21b7a2fdd011bea06bba7801b280e3151",
            fetch_token_prices(),
        )

        # initial data loaded from database
        self.feeds_data = self._init_feeds_data()
        self.refresh_feeds_data()
        self.refresh_predictoors_data()

        valid_addresses = list(self.predictoors_data["user"].str.to_lowercase())
        self.favourite_addresses = [
            addr for addr in ppss.predictoor_ss.my_addresses if addr in valid_addresses
        ]

    @property
    def start_date_ms(self) -> int:
        return UnixTimeMs.from_dt(self.start_date) if self.start_date else None

    @enforce_types
    def set_start_date_from_period(self, period: int):
        start_dt = (
            datetime.now(tz=timezone.utc) - timedelta(days=period)
            if int(period) > 0
            else None
        )
        self.start_date = start_dt
        self.file_reader.set_start_date(start_dt)

    @enforce_types
    def _init_feeds_data(self):
        df = self.file_reader._query_db(
            f"""
                SELECT contract, pair, timeframe, source
                FROM {tbl_parquet_path(self.lake_dir, BronzePrediction)}
                GROUP BY contract, pair, timeframe, source
            """,
            cache_file_name="feeds_data",
            periodical=False,
        )
        return df

    @enforce_types
    def _init_feed_payouts_stats(self) -> pl.DataFrame:
        query = f"""
                SELECT
                    p.contract,
                    SUM(p.stake) AS volume,
                    SUM(
                        CASE WHEN p.payout > 0
                        THEN 1 ELSE 0 END
                    ) * 100.0 / COUNT(*) AS avg_accuracy,
                    AVG(p.stake) AS avg_stake
                FROM
                    {tbl_parquet_path(self.lake_dir, BronzePrediction)} p
            """
        if self.start_date_ms:
            query += f"    WHERE timestamp > {self.start_date_ms}"

        query += """
            GROUP BY
                contract
            ORDER BY volume DESC
        """
        df = self.file_reader._query_db(query, cache_file_name="feed_payouts_stats")
        df.cast(
            {"avg_accuracy": pl.Float64, "avg_stake": pl.Float64, "volume": pl.Float64}
        )

        return df

    @enforce_types
    def _init_predictoor_payouts_stats(self) -> pl.DataFrame:

        query = f"""
            SELECT
                p."user",
                SUM(p.stake) AS total_stake,
                -- Calculate gross income: only include positive differences when payout > stake
                SUM(CASE WHEN p.payout > 0 THEN p.payout - p.stake ELSE 0 END) AS gross_income,
                -- Calculate total loss: sum up the negative income, capping positives at 0
                SUM(CASE WHEN p.payout = 0 THEN p.stake ELSE 0 END) AS stake_loss,
                SUM(p.payout) AS total_payout,
                -- Calculate total profit
                SUM(p.payout - p.stake) AS total_profit,
                -- Calculate total stake
                COUNT(p.ID) AS stake_count,
                COUNT(DISTINCT p.contract) AS feed_count,
                -- Count correct predictions where payout > 0
                SUM(CASE WHEN p.payout > 0 THEN 1 ELSE 0 END) AS correct_predictions,
                total_stake / stake_count AS avg_stake,
                MIN(p.slot) AS first_payout_time,
                MAX(p.slot) AS last_payout_time,
                -- Calculate the APR
                (SUM(p.payout - p.stake) / NULLIF(SUM(p.stake), 0)) * 100 AS apr,
                -- Calculate average accuracy
                SUM(CASE WHEN p.payout > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS avg_accuracy
            FROM
                {tbl_parquet_path(self.lake_dir, BronzePrediction)} p
        """

        if self.start_date_ms:
            query += f"    WHERE p.timestamp > {self.start_date_ms}"

        query += """
            GROUP BY
                p."user"
            ORDER BY
                apr DESC
        """

        df = self.file_reader._query_db(
            query, cache_file_name="predictoor_payouts_stats"
        )
        df.cast(
            {
                "avg_accuracy": pl.Float64,
                "total_stake": pl.Float64,
                "gross_income": pl.Float64,
                "stake_loss": pl.Float64,
            }
        )

        return df

    @enforce_types
    def _init_feed_subscription_stats(self) -> pl.DataFrame:
        opf_addresses = get_opf_addresses(self.network_name)

        query = f"""
            WITH ws_buy_counts AS (
                SELECT
                    SPLIT_PART(ID, '-', 1) AS contract,
                    COUNT(*) AS ws_buy_count
                FROM
                    {tbl_parquet_path(self.lake_dir, Subscription)}
                WHERE
                    "user" = '{opf_addresses["websocket"].lower()}'
                """
        if self.start_date_ms:
            query += f"AND timestamp > {self.start_date_ms}"

        query += f"""
                GROUP BY
                    SPLIT_PART(ID, '-', 1)
            ),
            user_buy_counts AS (
                SELECT
                    SPLIT_PART(ID, '-', 1) AS contract,
                    COUNT(*) AS df_buy_count
                FROM
                    {tbl_parquet_path(self.lake_dir, Subscription)}
                WHERE
                    "user" = '{opf_addresses["dfbuyer"].lower()}'
                """
        if self.start_date_ms:
            query += f"AND timestamp > {self.start_date_ms}"

        query += f"""
                GROUP BY
                    SPLIT_PART(ID, '-', 1)
            )
            SELECT
                main_contract AS contract,
                SUM(last_price_value) AS sales_revenue,
                AVG(last_price_value) AS price,
                COUNT(*) AS sales,
                COALESCE(ubc.df_buy_count, 0) AS df_buy_count,
                COALESCE(wbc.ws_buy_count, 0) AS ws_buy_count
            FROM
                (
                    SELECT
                        SPLIT_PART(ID, '-', 1) AS main_contract,
                        last_price_value
                    FROM
                        {tbl_parquet_path(self.lake_dir, Subscription)}
            """

        if self.start_date_ms:
            query += f"WHERE timestamp > {self.start_date_ms}"

        query += """
                ) AS main
            LEFT JOIN
                user_buy_counts ubc
            ON
                main.main_contract = ubc.contract
            LEFT JOIN
                ws_buy_counts wbc
            ON
                main.main_contract = wbc.contract
            GROUP BY
                main_contract, ubc.df_buy_count, wbc.ws_buy_count
        """

        df = self.file_reader._query_db(
            query, cache_file_name="feed_subscription_stats"
        )
        df.cast({"sales_revenue": pl.Float64, "price": pl.Float64})

        return df

    @enforce_types
    def feed_daily_subscriptions_by_feed_id(self, feed_id: str) -> pl.DataFrame:
        query = f"""
            WITH date_counts AS (
                SELECT
                    CAST(TO_TIMESTAMP(timestamp / 1000) AS DATE) AS day,
                    COUNT(*) AS count,
                    SUM(last_price_value) AS revenue
                FROM
                    {tbl_parquet_path(self.lake_dir, Subscription)}
                WHERE
                    ID LIKE '%{feed_id}%'
        """
        if self.start_date_ms:
            query += f" AND timestamp > {self.start_date_ms}"

        query += """
            GROUP BY
                    day
            )
            SELECT * FROM date_counts
            ORDER BY day;
        """

        return self.file_reader._query_db(query)

    @enforce_types
    def feed_ids_based_on_predictoors(
        self, predictoor_addrs: Optional[List] = None
    ) -> List[str]:
        if not predictoor_addrs and not self.favourite_addresses:
            return []

        if not predictoor_addrs:
            predictoor_addrs = self.favourite_addresses

        assert isinstance(predictoor_addrs, list)

        # Constructing the SQL query
        query = f"""
            SELECT LIST(DISTINCT p.contract) as feed_addrs
            FROM {tbl_parquet_path(self.lake_dir, BronzePrediction)} p
            WHERE p.contract IN (
                SELECT MIN(p.contract)
                FROM {tbl_parquet_path(self.lake_dir, BronzePrediction)} p
                WHERE (
                    {" OR ".join([f"p.user LIKE '%{item}%'" for item in predictoor_addrs])}
                )
                GROUP BY p.contract
            );
        """

        # Execute the query
        return self.file_reader._query_db(query, scalar=True)

    @enforce_types
    def payouts_from_bronze_predictions(
        self,
        feed_addrs: Optional[List],
        predictoor_addrs: Optional[List],
    ) -> List[dict]:
        """
        Get predictions data for the given feed and
        predictoor addresses from the bronze_pdr_predictions table.
        Args:
            feed_addrs (list): List of feed addresses.
            predictoor_addrs (list): List of predictoor addresses.
            start_date (int): The starting slot (timestamp)
                for filtering the results.
        Returns:
            list: List of predictions data.
        """

        # Start constructing the SQL query
        query = f"""SELECT * FROM
                {tbl_parquet_path(self.lake_dir, BronzePrediction)}
            """

        # List to hold the WHERE clause conditions
        conditions = []

        # Adding conditions for feed addresses if provided
        if feed_addrs:
            feed_conditions = " OR ".join(
                [f"contract = '{addr}'" for addr in feed_addrs]
            )
            conditions.append(f"({feed_conditions})")

        # Adding conditions for predictoor addresses if provided
        if predictoor_addrs:
            predictoor_conditions = " OR ".join(
                [f"user = '{addr}'" for addr in predictoor_addrs]
            )
            conditions.append(f"({predictoor_conditions})")

        # Adding condition for the start date if provided
        if self.start_date_ms:
            conditions.append(f"timestamp >= {self.start_date_ms}")

        # If there are any conditions, append them to the query
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # ORDER BY slot
        query += " ORDER BY slot;"

        # Execute the query without passing parameters

        result = self.file_reader._query_db(query)
        result = result.fill_null(0)

        return result

    @enforce_types
    def feeds_metrics(self) -> dict[str, Union[int, float]]:
        query_feeds = f"""
            SELECT COUNT(DISTINCT(contract, pair, timeframe, source))
            FROM {tbl_parquet_path(self.lake_dir, Prediction)}
        """
        if self.start_date_ms:
            query_feeds += f"WHERE timestamp > {self.start_date_ms}"
        feeds = self.file_reader._query_db(
            query_feeds, scalar=True, cache_file_name="feeds"
        )

        query_payouts = f"""
            SELECT
                SUM(
                    CASE WHEN p.payout > 0
                    THEN 1 ELSE 0 END
                ) * 100.0 / COUNT(*) AS avg_accuracy,
                SUM(p.stake) AS total_stake
            FROM
                {tbl_parquet_path(self.lake_dir, BronzePrediction)} p
        """
        if self.start_date_ms:
            query_payouts += f"WHERE timestamp > {self.start_date_ms}"
        accuracy, volume = self.file_reader._query_db(
            query_payouts, scalar=True, cache_file_name="feeds_accuracy"
        )

        query_subscriptions = f"""
            SELECT COUNT(ID),
            SUM(last_price_value)
            FROM {tbl_parquet_path(self.lake_dir, Subscription)}
        """

        if self.start_date_ms:
            query_subscriptions += f" WHERE timestamp > {self.start_date_ms}"

        sales, revenue = self.file_reader._query_db(
            query_subscriptions, scalar=True, cache_file_name="sales_revenue"
        )

        return {
            "Feeds": feeds if feeds else 0,
            "Accuracy": accuracy if accuracy else 0.0,
            "Volume": volume if volume else 0,
            "Sales": sales if sales else 0,
            "Revenue": revenue if revenue else 0,
        }

    @enforce_types
    def predictoors_metrics(self) -> dict[str, Union[int, float]]:
        query_predictoors_metrics = f"""
                SELECT
                    COUNT(DISTINCT(user)) AS predictoors,
                    SUM(
                        CASE WHEN p.payout > 0
                        THEN 1 ELSE 0 END
                    ) * 100 / COUNT(*) AS avg_accuracy,
                    SUM(p.stake) AS tot_stake,
                    SUM(
                        CASE WHEN p.payout > p.stake
                        THEN p.payout - p.stake ELSE 0 END
                    ) AS tot_gross_income
                FROM
                    {tbl_parquet_path(self.lake_dir, BronzePrediction)} p
            """
        if self.start_date_ms:
            query_predictoors_metrics += f" WHERE timestamp > {self.start_date_ms}"
        predictoors, avg_accuracy, tot_stake, tot_gross_income = (
            self.file_reader._query_db(
                query_predictoors_metrics,
                scalar=True,
                cache_file_name="predictoor_metrics_predictoors",
            )
        )

        return {
            "Predictoors": predictoors,
            "Accuracy(avg)": avg_accuracy,
            "Staked": tot_stake,
            "Gross Income": tot_gross_income,
        }

    def get_first_and_last_slot_timestamp(self) -> Tuple[UnixTimeS, UnixTimeS]:
        first_timestamp, last_timestamp = self.file_reader._query_db(
            f"""
                SELECT
                    MIN(timestamp) as min,
                    MAX(timestamp) as max
                FROM
                    {tbl_parquet_path(self.lake_dir, Slot)}
            """,
            scalar=True,
            cache_file_name="first_and_last_slot_timestamp",
            periodical=False,
        )
        return (
            UnixTimeMs(first_timestamp).to_seconds(),
            UnixTimeMs(last_timestamp).to_seconds(),
        )

    @enforce_types
    def refresh_feeds_data(self) -> None:
        self.feeds_metrics_data = self.feeds_metrics()
        self.feeds_payout_stats = self._init_feed_payouts_stats()
        self.feeds_subscriptions = self._init_feed_subscription_stats()

        # data formatting for tables, columns and raw data
        self.feeds_table_data, self.raw_feeds_data = (
            self._formatted_data_for_feeds_table
        )

    @enforce_types
    def refresh_predictoors_data(self) -> None:
        self.predictoors_metrics_data = self.predictoors_metrics()
        self.predictoors_data = self._init_predictoor_payouts_stats()

        # data formatting for tables, columns and raw data
        # pylint: disable=unbalanced-tuple-unpacking
        self.predictoors_table_data, self.raw_predictoors_data = (
            self._formatted_data_for_predictoors_table
        )

    @property
    @enforce_types
    def _formatted_data_for_feeds_table(
        self,
    ) -> Tuple[pl.DataFrame, pl.DataFrame]:
        df = self.feeds_data.clone()
        df = df.with_columns(
            pl.col("contract").alias("full_addr"),
            pl.col("contract").alias("addr"),
            pl.col("pair")
            .str.split_exact("/", 1)
            .map_elements(lambda x: x["field_0"], return_dtype=pl.String)
            .alias("base_token"),
            pl.col("pair")
            .str.split_exact("/", 1)
            .map_elements(lambda x: x["field_1"], return_dtype=pl.String)
            .alias("quote_token"),
            pl.col("source").str.to_titlecase().alias("source"),
            pl.lit("").alias("sales_str"),
        )
        df = df.join(self.feeds_payout_stats, on="contract")
        df = df.join(self.feeds_subscriptions, on="contract")
        df = df.fill_null(0)

        columns = [col["id"] for col in FEEDS_TABLE_COLS]
        df = df[columns]

        formatted_data = df.clone()
        formatted_data = format_df(formatted_data)

        return formatted_data, df

    @property
    @enforce_types
    def _formatted_data_for_predictoors_table(
        self,
    ) -> Tuple[pl.DataFrame, pl.DataFrame]:
        df = self.predictoors_data.clone()
        df = df.with_columns(
            pl.col("user").alias("full_addr"),
            pl.col("user").alias("addr"),
            pl.col("stake_count").mul(self.fee_cost).alias("tx_costs_(OCEAN)"),
        )
        df = df.fill_null(0)
        df = df.with_columns(
            pl.struct(["total_profit", "tx_costs_(OCEAN)"])
            .map_elements(
                lambda x: x["total_profit"] - x["tx_costs_(OCEAN)"],
                return_dtype=pl.Float64,
            )
            .alias("net_income_(OCEAN)")
        )

        columns = [col["id"] for col in PREDICTOORS_TABLE_COLS]

        df = df[columns]

        formatted_data = df.clone()
        formatted_data = format_df(formatted_data)

        return formatted_data, df

    @enforce_types
    def filter_for_feeds_table(
        self,
        predictoor_feeds_only: bool,
        predictoors_addrs: List[str],
        search_value: Optional[str],
        selected_feeds_addrs: List[str],
    ) -> List[dict]:
        filtered_data = self.formatted_feeds_home_page_table_data.clone()

        # filter feeds by payouts from selected predictoors
        if predictoor_feeds_only and (len(predictoors_addrs) > 0):
            feed_ids = self.feed_ids_based_on_predictoors(
                predictoors_addrs,
            )
            filtered_data = filtered_data.filter(
                filtered_data["contract"].is_in(feed_ids)
            )

        if search_value:
            filtered_data = filtered_data.filter(
                filtered_data["pair"].str.contains(search_value)
            )

        filtered_data = filtered_data.filter(
            ~filtered_data["contract"].is_in(selected_feeds_addrs)
        )
        selected_feeds = self.formatted_feeds_home_page_table_data.filter(
            self.formatted_feeds_home_page_table_data["contract"].is_in(
                selected_feeds_addrs
            )
        )

        return pl.concat([selected_feeds, filtered_data]).to_dicts()

    @property
    @enforce_types
    def formatted_predictoors_home_page_table_data(self) -> pl.DataFrame:
        """
        Process the user payouts stats data.
        Args:
            user_payout_stats (list): List of user payouts stats data.
        Returns:
            list: List of processed user payouts stats data.
        """
        df = self.predictoors_data.clone()
        df = df.with_columns(
            pl.col("user").alias("full_addr"),
            pl.col("user").alias("addr"),
        )
        df = df.fill_null(0)

        cols = [col["id"] for col in PREDICTOORS_HOME_PAGE_TABLE_COLS]

        return format_df(df[cols])

    @property
    @enforce_types
    def formatted_feeds_home_page_table_data(self) -> pl.DataFrame:
        df = self.feeds_data.clone()
        df = df.join(self.feeds_payout_stats, on="contract")
        df = df.join(self.feeds_subscriptions, on="contract")
        df = df.fill_nan(0)

        columns = [col["id"] for col in FEEDS_HOME_PAGE_TABLE_COLS]

        return format_df(df[columns])

    @property
    @enforce_types
    def homepage_feeds_cols(self) -> Tuple[Tuple, pl.DataFrame]:
        data = self.formatted_feeds_home_page_table_data

        columns = FEEDS_HOME_PAGE_TABLE_COLS
        hidden_columns = ["contract"]

        return (columns, hidden_columns), data

    @property
    @enforce_types
    def homepage_predictoors_cols(self) -> Tuple[Tuple, pl.DataFrame]:
        data = self.formatted_predictoors_home_page_table_data.clone()

        if self.favourite_addresses:
            df1 = data.filter(data["full_addr"].is_in(self.favourite_addresses))
            df2 = data.filter(~data["full_addr"].is_in(self.favourite_addresses))
            data = pl.concat([df1, df2])

        columns = PREDICTOORS_HOME_PAGE_TABLE_COLS
        hidden_columns = ["full_addr"]

        return (columns, hidden_columns), data
