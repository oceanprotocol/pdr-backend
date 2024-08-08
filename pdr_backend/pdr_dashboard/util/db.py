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

    @enforce_types
    def payouts(
        self, feed_addrs: List[str], predictoor_addrs: List[str], start_date: int
    ) -> List[dict]:
        """
        Get payouts data for the given feed and predictoor addresses.
        Args:
            feed_addrs (list): List of feed addresses.
            predictoor_addrs (list): List of predictoor addresses.
        Returns:
            list: List of payouts data.
        """

        # Constructing the SQL query
        query = f"SELECT * FROM {Payout.get_lake_table_name()} WHERE ("

        # Adding conditions for the first list
        query += " OR ".join([f"ID LIKE '%{item}%'" for item in feed_addrs])
        query += ") AND ("

        # Adding conditions for the second list
        query += " OR ".join([f"ID LIKE '%{item}%'" for item in predictoor_addrs])
        query += ")"
        if start_date != 0:
            query += f"AND (slot >= {start_date})"
        query += ";"

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
            "Accuracy": str(round(accuracy, 2) if accuracy else 0.0) + "%",
            "Volume": str(round(volume, 2) if volume else 0.0) + " OCEAN",
            "Sales": sales if sales else 0,
            "Revenue": str(round(revenue, 2) if revenue else 0.0) + " OCEAN",
        }
