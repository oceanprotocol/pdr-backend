import logging

from typing import Union, List
from enforce_typing import enforce_types

from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.payout import Payout
from pdr_backend.lake.prediction import Prediction
from pdr_backend.lake.subscription import Subscription
from pdr_backend.util.constants_opf_addrs import get_opf_addresses

logger = logging.getLogger("predictoor_dashboard_utils")


class DBGetter:
    def __init__(self, lake_dir: str):
        self.lake_dir = lake_dir

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
                result = df.to_dicts() if len(df) else []

            db.duckdb_conn.close()
            return result
        except Exception as e:
            logger.error("Error querying the database: %s", e)
            return []

    @enforce_types
    def feeds_data(self):
        return self._query_db(
            f"""
                SELECT contract, pair, timeframe, source FROM {Prediction.get_lake_table_name()}
                GROUP BY contract, pair, timeframe, source
            """,
        )

    @enforce_types
    def predictoors_data(self):
        return self._query_db(
            f"""
                SELECT user FROM {Prediction.get_lake_table_name()}
                GROUP BY user
            """,
        )

    @enforce_types
    def payouts_stats(self):
        return self._query_db(
            f"""
                SELECT
                    "user",
                    SUM(payout - stake) AS total_profit,
                    SUM(CASE WHEN payout > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS avg_accuracy,
                    AVG(stake) AS avg_stake
                FROM
                    {Payout.get_lake_table_name()}
                GROUP BY
                    "user"
            """,
        )

    @enforce_types
    def feed_payouts_stats(self):
        return self._query_db(
            f"""
                SELECT
                    SPLIT_PART(ID, '-', 1) AS contract,
                    SUM(stake) AS volume,
                    SUM(CASE WHEN payout > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS avg_accuracy,
                    AVG(stake) AS avg_stake
                FROM
                    {Payout.get_lake_table_name()}
                GROUP BY
                    contract
            """,
        )

    @enforce_types
    def predictoor_payouts_stats(self):
        # Insert the generated CASE clause into the SQL query
        query = f"""
            SELECT
                p."user",
                SUM(p.stake) AS total_stake,
                -- Calculate gross income: only include positive differences when payout > stake
                SUM(CASE WHEN p.payout > 0 THEN p.payout - p.stake ELSE 0 END) AS gross_income,
                -- Calculate total loss: sum up the negative income, capping positives at 0
                SUM(CASE WHEN p.payout = 0 THEN p.stake ELSE 0 END) AS stake_loss,
                SUM(p.payout) AS total_payout,
                --- Calculate total profit
                SUM(p.payout - p.stake) AS total_profit,
                --- Calculate total stake
                SUM(p.stake) AS total_stake,
                COUNT(p.ID) AS stake_count,
                COUNT(DISTINCT SPLIT_PART(p.ID, '-', 1)) AS feed_count,
                -- Count correct predictions where payout > 0
                SUM(CASE WHEN p.payout > 0 THEN 1 ELSE 0 END) AS correct_predictions,
                COUNT(*) AS predictions,
                AVG(p.stake) AS avg_stake,
                MIN(p.slot) AS first_payout_time,
                MAX(p.slot) AS last_payout_time,
                -- Calculate the APR
                total_profit / total_stake * 100 AS apr,
                -- Calculate average accuracy
                SUM(CASE WHEN p.payout > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS avg_accuracy
            FROM
                {Payout.get_lake_table_name()} p
            GROUP BY
                p."user";
        """

        return self._query_db(query)

    @enforce_types
    def feed_subscription_stats(self, network_name: str):
        opf_addresses = get_opf_addresses(network_name)

        query = f"""
            WITH ws_buy_counts AS (
                SELECT
                    SPLIT_PART(ID, '-', 1) AS contract,
                    COUNT(*) AS ws_buy_count
                FROM
                    {Subscription.get_lake_table_name()}
                WHERE
                    "user" = '{opf_addresses["websocket"].lower()}'
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
                main_contract, ubc.df_buy_count, wbc.ws_buy_count"""

        return self._query_db(query)

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
            GROUP BY
                day
        )
        SELECT * FROM date_counts
        ORDER BY day;
        """

        return self._query_db(query)

    def feed_ids_based_on_predictoors(self, predictoor_addrs: List[str]):
        # Constructing the SQL query
        query = f"""
            SELECT LIST(LEFT(ID, POSITION('-' IN ID) - 1)) as feed_addrs
            FROM {Payout.get_lake_table_name()}
            WHERE ID IN (
                SELECT MIN(ID)
                FROM {Payout.get_lake_table_name()}
                WHERE (
                    {" OR ".join([f"ID LIKE '%{item}%'" for item in predictoor_addrs])}
                )
                GROUP BY LEFT(ID, POSITION('-' IN ID) - 1)
            );
        """

        # Execute the query
        return self._query_db(query, scalar=True)

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
            conditions.append("slot >= %s")

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
    def feeds_stats(self):
        feeds = self._query_db(
            f"""
                SELECT COUNT(DISTINCT(contract, pair, timeframe, source))
                FROM {Prediction.get_lake_table_name()}
            """,
            scalar=True,
        )

        accuracy, volume = self._query_db(
            f"""
                SELECT
                    SUM(CASE WHEN payout > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS avg_accuracy,
                    SUM(stake) AS total_stake
                FROM
                    {Payout.get_lake_table_name()}
            """,
            scalar=True,
        )

        sales, revenue = self._query_db(
            f"SELECT COUNT(ID), SUM(last_price_value) from {Subscription.get_lake_table_name()}",
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
    def predictoors_stats(self):
        predictoors = self._query_db(
            f"""
                SELECT COUNT(DISTINCT(user))
                FROM {Prediction.get_lake_table_name()}
            """,
            scalar=True,
        )

        avg_accuracy, tot_stake, tot_gross_income = self._query_db(
            f"""
                SELECT
                    SUM(CASE WHEN payout > 0 THEN 1 ELSE 0 END) * 100 / COUNT(*) AS avg_accuracy,
                    SUM(stake) as tot_stake,
                    SUM(CASE WHEN payout > stake THEN payout - stake ELSE 0 END) AS tot_gross_income
                FROM
                    {Payout.get_lake_table_name()}
            """,
            scalar=True,
        )

        return {
            "Predictoors": predictoors,
            "Accuracy(avg)": avg_accuracy,
            "Staked": tot_stake,
            "Gross Income": tot_gross_income,
        }
