import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas
from enforce_typing import enforce_types

from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.payout import Payout
from pdr_backend.lake.prediction import Prediction
from pdr_backend.lake.slot import Slot
from pdr_backend.lake.subscription import Subscription
from pdr_backend.lake.table_bronze_pdr_predictions import BronzePrediction
from pdr_backend.pdr_dashboard.util.data import get_sales_str
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
from pdr_backend.util.constants_opf_addrs import get_opf_addresses
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("predictoor_dashboard_utils")


# pylint: disable=too-many-instance-attributes
class AppDataManager:
    def __init__(self, ppss):
        self.lake_dir = ppss.lake_ss.lake_dir
        self.network_name = ppss.web3_pp.network
        self.start_date: Optional[datetime] = None

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

        valid_addresses = list(self.predictoors_data["user"].str.lower())
        self.favourite_addresses = [
            addr for addr in ppss.predictoor_ss.my_addresses if addr in valid_addresses
        ]

    @property
    def start_date_ms(self) -> int:
        return UnixTimeMs.from_dt(self.start_date) if self.start_date else None

    def set_start_date_from_period(self, period: int):
        start_dt = datetime.now() - timedelta(days=period) if int(period) > 0 else None
        self.start_date = start_dt

    @enforce_types
    def _query_db(self, query: str, scalar=False) -> Union[List[dict], Exception]:
        """
        Query the database with the given query.
        Args:
            query (str): SQL query.
        Returns:
            dict: Query result.
        """
        try:
            db = DuckDBDataStore(self.lake_dir, read_only=True)

            if scalar:
                result = db.query_scalar(query)
            else:
                df = db.query_data(query)
                result = df.to_pandas()

            db.duckdb_conn.close()
            return result
        except Exception as e:
            logger.error("Error querying the database: %s", e)
            return pandas.DataFrame()

    @enforce_types
    def _init_feeds_data(self):
        df = self._query_db(
            f"""
                SELECT contract, pair, timeframe, source
                FROM {BronzePrediction.get_lake_table_name()}
                GROUP BY contract, pair, timeframe, source
            """,
        )
        return df

    @enforce_types
    def _init_feed_payouts_stats(self):
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
                    {BronzePrediction.get_lake_table_name()} p
            """
        if self.start_date_ms:
            query += f"    WHERE timestamp > {self.start_date_ms}"

        query += """
            GROUP BY
                contract
            ORDER BY volume DESC;
        """
        df = self._query_db(query)

        df["avg_accuracy"] = df["avg_accuracy"].astype(float)
        df["avg_stake"] = df["avg_stake"].astype(float)
        df["volume"] = df["volume"].astype(float)

        return df

    @enforce_types
    def _init_predictoor_payouts_stats(self):

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
                {BronzePrediction.get_lake_table_name()} p
        """

        if self.start_date_ms:
            query += f"    WHERE p.timestamp > {self.start_date_ms}"

        query += """
            GROUP BY
                p."user"
            ORDER BY
                apr DESC;
        """
        df = self._query_db(query)

        df["avg_accuracy"] = df["avg_accuracy"].astype(float)
        df["total_stake"] = df["total_stake"].astype(float)
        df["gross_income"] = df["gross_income"].astype(float)
        df["stake_loss"] = df["stake_loss"].astype(float)

        return df

    @enforce_types
    def _init_feed_subscription_stats(self):
        opf_addresses = get_opf_addresses(self.network_name)

        query = f"""
            WITH ws_buy_counts AS (
                SELECT
                    SPLIT_PART(ID, '-', 1) AS contract,
                    COUNT(*) AS ws_buy_count
                FROM
                    {Subscription.get_lake_table_name()}
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
                    {Subscription.get_lake_table_name()}
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
                        {Subscription.get_lake_table_name()}
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

        df = self._query_db(query)
        df["sales_revenue"] = df["sales_revenue"].astype(float)
        df["price"] = df["price"].astype(float)

        return df

    @enforce_types
    def feed_daily_subscriptions_by_feed_id(self, feed_id: str):
        query = f"""
            WITH date_counts AS (
                SELECT
                    CAST(TO_TIMESTAMP(timestamp / 1000) AS DATE) AS day,
                    COUNT(*) AS count,
                    SUM(last_price_value) AS revenue
                FROM
                    {Subscription.get_lake_table_name()}
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

        return self._query_db(query)

    def feed_ids_based_on_predictoors(
        self, predictoor_addrs: Optional[List[str]] = None
    ):
        if not predictoor_addrs and not self.favourite_addresses:
            return []

        if not predictoor_addrs:
            predictoor_addrs = self.favourite_addresses

        assert isinstance(predictoor_addrs, list)

        # Constructing the SQL query
        query = f"""
            SELECT LIST(DISTINCT p.contract) as feed_addrs
            FROM bronze_pdr_predictions p
            WHERE p.contract IN (
                SELECT MIN(p.contract)
                FROM {BronzePrediction.get_lake_table_name()} p
                WHERE (
                    {" OR ".join([f"p.user LIKE '%{item}%'" for item in predictoor_addrs])}
                )
                GROUP BY p.contract
            );
        """

        # Execute the query
        return self._query_db(query, scalar=True)

    def payouts_from_bronze_predictions(
        self,
        feed_addrs: Union[List[str], None],
        predictoor_addrs: Union[List[str], None],
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
        query = f"SELECT * FROM {BronzePrediction.get_lake_table_name()}"

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

        query += ";"

        # Execute the query without passing parameters
        return self._query_db(query)

    def payouts(
        self,
        feed_addrs: Union[List[str], None],
        predictoor_addrs: Union[List[str], None],
        start_date: int,
    ) -> List[dict]:
        """
        Get payouts data for the given feed and predictoor addresses.
        Args:
            feed_addrs (list): List of feed addresses.
            predictoor_addrs (list): List of predictoor addresses.
            start_date (int): The starting slot (timestamp) for filtering the results.
        Returns:
            list: List of payouts data.
        """

        # Start constructing the SQL query
        query = f"SELECT * FROM {Payout.get_lake_table_name()}"

        # List to hold the WHERE clause conditions
        conditions = []

        # Adding conditions for feed addresses if provided
        if feed_addrs:
            feed_conditions = " OR ".join(["ID LIKE %s" for _ in feed_addrs])
            conditions.append(f"({feed_conditions})")

        # Adding conditions for predictoor addresses if provided
        if predictoor_addrs:
            predictoor_conditions = " OR ".join(
                ["ID LIKE %s" for _ in predictoor_addrs]
            )
            conditions.append(f"({predictoor_conditions})")

        # Adding condition for the start date if provided
        if start_date:
            conditions.append("timestamp >= %s")

        # If there are any conditions, append them to the query
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += ";"

        # List of parameters to prevent SQL injection
        params = []
        if feed_addrs:
            params.extend([f"'%{item}%'" for item in feed_addrs])
        if predictoor_addrs:
            params.extend([f"'%{item}%'" for item in predictoor_addrs])
        if start_date:
            params.append(str(start_date))

        query = query % tuple(params)

        # Execute the query
        return self._query_db(query)

    @enforce_types
    def feeds_metrics(self) -> dict[str, Any]:
        query_feeds = f"""
            SELECT COUNT(DISTINCT(contract, pair, timeframe, source))
            FROM {Prediction.get_lake_table_name()}
        """
        if self.start_date_ms:
            query_feeds += f"WHERE timestamp > {self.start_date_ms}"
        feeds = self._query_db(
            query_feeds,
            scalar=True,
        )

        query_payouts = f"""
            SELECT
                SUM(
                    CASE WHEN p.payout > 0
                    THEN 1 ELSE 0 END
                ) * 100.0 / COUNT(*) AS avg_accuracy,
                SUM(p.stake) AS total_stake
            FROM
                {BronzePrediction.get_lake_table_name()} p
        """
        if self.start_date_ms:
            query_payouts += f"WHERE timestamp > {self.start_date_ms}"
        accuracy, volume = self._query_db(
            query_payouts,
            scalar=True,
        )

        query_subscriptions = f"""
            SELECT COUNT(ID),
            SUM(last_price_value)
            FROM {Subscription.get_lake_table_name()}
        """
        if self.start_date_ms:
            query_subscriptions += f" WHERE timestamp > {self.start_date_ms}"
        sales, revenue = self._query_db(
            query_subscriptions,
            scalar=True,
        )

        return {
            "Feeds": feeds if feeds else 0,
            "Accuracy": accuracy if accuracy else 0.0,
            "Volume": volume if volume else 0,
            "Sales": sales if sales else 0,
            "Revenue": revenue if revenue else 0,
        }

    @enforce_types
    def predictoors_metrics(self) -> dict[str, Any]:
        query_predictions = f"""
            SELECT COUNT(DISTINCT(user))
            FROM {Prediction.get_lake_table_name()}
        """
        if self.start_date_ms:
            query_predictions += f" WHERE timestamp > {self.start_date_ms}"
        predictoors = self._query_db(
            query_predictions,
            scalar=True,
        )

        query_payouts = f"""
                SELECT
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
                    {BronzePrediction.get_lake_table_name()} p
            """
        if self.start_date_ms:
            query_payouts += f" WHERE timestamp > {self.start_date_ms}"
        avg_accuracy, tot_stake, tot_gross_income = self._query_db(
            query_payouts,
            scalar=True,
        )

        return {
            "Predictoors": predictoors,
            "Accuracy(avg)": avg_accuracy,
            "Staked": tot_stake,
            "Gross Income": tot_gross_income,
        }

    def get_first_and_last_slot_timestamp(self):
        first_timestamp, last_timestamp = self._query_db(
            f"""
                SELECT
                    MIN(timestamp) as min,
                    MAX(timestamp) as max
                FROM
                    {Slot.get_lake_table_name()}
            """,
            scalar=True,
        )
        return first_timestamp / 1000, last_timestamp / 1000

    def refresh_feeds_data(self):
        self.feeds_metrics_data = self.feeds_metrics()
        self.feeds_payout_stats = self._init_feed_payouts_stats()
        self.feeds_subscriptions = self._init_feed_subscription_stats()

        # data formatting for tables, columns and raw data
        self.feeds_table_data, self.raw_feeds_data = (
            self._formatted_data_for_feeds_table
        )

    def refresh_predictoors_data(self):
        self.predictoors_metrics_data = self.predictoors_metrics()
        self.predictoors_data = self._init_predictoor_payouts_stats()

        # data formatting for tables, columns and raw data
        # pylint: disable=unbalanced-tuple-unpacking
        self.predictoors_table_data, self.raw_predictoors_data = (
            self._formatted_data_for_predictoors_table
        )

    @property
    def _formatted_data_for_feeds_table(
        self,
    ) -> Tuple[pandas.DataFrame, pandas.DataFrame]:
        df = self.feeds_data.copy()
        df["addr"] = df["full_addr"] = df["contract"]
        df[["base_token", "quote_token"]] = df["pair"].str.split("/", expand=True)
        df["source"] = df["source"].str.capitalize()
        df = df.merge(self.feeds_payout_stats, on="contract")
        df = df.merge(self.feeds_subscriptions, on="contract")
        df["sales_str"] = df.apply(get_sales_str, axis=1)
        df["sales_raw"] = df["sales"]
        df.fillna(0, inplace=True)

        columns = [col["id"] for col in FEEDS_TABLE_COLS]
        df = df[columns]

        formatted_data = df.copy()
        formatted_data = format_df(formatted_data)

        return formatted_data, df

    @property
    def _formatted_data_for_predictoors_table(
        self,
    ) -> Tuple[pandas.DataFrame, pandas.DataFrame]:
        df = self.predictoors_data.copy()
        df["addr"] = df["full_addr"] = df["user"]
        df["tx_costs_(OCEAN)"] = df["stake_count"] * self.fee_cost
        df.fillna(0, inplace=True)
        df["net_income_(OCEAN)"] = df["total_profit"] - df["tx_costs_(OCEAN)"]

        columns = [col["id"] for col in PREDICTOORS_TABLE_COLS]

        df = df[columns]

        formatted_data = df.copy()
        formatted_data = format_df(formatted_data)

        return formatted_data, df

    def filter_for_feeds_table(
        self,
        predictoor_feeds_only,
        predictoors_addrs,
        search_value,
        selected_feeds_addrs,
    ):
        filtered_data = self.formatted_feeds_home_page_table_data.copy()

        # filter feeds by payouts from selected predictoors
        if predictoor_feeds_only and (len(predictoors_addrs) > 0):
            feed_ids = self.feed_ids_based_on_predictoors(
                predictoors_addrs,
            )
            filtered_data = filtered_data[filtered_data["contract"].isin(feed_ids)]

        if search_value:
            filtered_data = filtered_data[
                filtered_data["pair"].str.contains(search_value)
            ]

        filtered_data = filtered_data[
            ~filtered_data["contract"].isin(selected_feeds_addrs)
        ]
        selected_feeds = self.formatted_feeds_home_page_table_data[
            self.formatted_feeds_home_page_table_data["contract"].isin(
                selected_feeds_addrs
            )
        ]

        return pandas.concat([selected_feeds, filtered_data]).to_dict("records")

    @property
    @enforce_types
    def formatted_predictoors_home_page_table_data(self) -> List[Dict[str, Any]]:
        """
        Process the user payouts stats data.
        Args:
            user_payout_stats (list): List of user payouts stats data.
        Returns:
            list: List of processed user payouts stats data.
        """
        df = self.predictoors_data.copy()
        df["addr"] = df["full_addr"] = df["user"]
        df.fillna(0, inplace=True)

        cols = [col["id"] for col in PREDICTOORS_HOME_PAGE_TABLE_COLS]

        formatted_data = df.copy()
        formatted_data = formatted_data[cols]
        return format_df(formatted_data)

    @property
    @enforce_types
    def formatted_feeds_home_page_table_data(self):
        df = self.feeds_data.copy()
        df = df.merge(self.feeds_payout_stats, on="contract")
        df = df.merge(self.feeds_subscriptions, on="contract")
        df["sales_raw"] = df["sales"]
        df.fillna(0, inplace=True)

        columns = [col["id"] for col in FEEDS_HOME_PAGE_TABLE_COLS]
        df = df[columns]

        formatted_data = df.copy()
        formatted_data = format_df(formatted_data)

        return formatted_data

    @property
    def homepage_feeds_cols(self):
        data = self.formatted_feeds_home_page_table_data

        columns = FEEDS_HOME_PAGE_TABLE_COLS
        hidden_columns = ["contract"]

        return (columns, hidden_columns), data

    @property
    def homepage_predictoors_cols(self):
        data = self.formatted_predictoors_home_page_table_data

        if self.favourite_addresses:
            df = data.copy()
            df1 = df[df["full_addr"].isin(self.favourite_addresses)]
            df2 = df[~df["full_addr"].isin(self.favourite_addresses)]
            data = pandas.concat([df1, df2])

        columns = PREDICTOORS_HOME_PAGE_TABLE_COLS
        hidden_columns = ["full_addr"]

        return (columns, hidden_columns), data
