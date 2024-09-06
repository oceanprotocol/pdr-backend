import logging
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple, Union

from enforce_typing import enforce_types

from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.payout import Payout
from pdr_backend.lake.prediction import Prediction
from pdr_backend.lake.subscription import Subscription
from pdr_backend.lake.slot import Slot
from pdr_backend.pdr_dashboard.util.data import (
    col_to_human,
    filter_objects_by_field,
    get_feed_column_ids,
    get_feeds_stat_with_contract,
    get_feeds_subscription_stat_with_contract,
)
from pdr_backend.pdr_dashboard.util.format import format_dict, format_table
from pdr_backend.pdr_dashboard.util.prices import (
    calculate_tx_gas_fee_cost_in_OCEAN,
    fetch_token_prices,
)
from pdr_backend.util.constants_opf_addrs import get_opf_addresses

logger = logging.getLogger("predictoor_dashboard_utils")

PREDICTOORS_HOME_PAGE_TABLE_COLS = [
    {"name": "Addr", "id": "addr"},
    {"name": "Full Addr", "id": "full_addr"},
    {"name": "Apr", "id": "apr"},
    {"name": "Accuracy", "id": "accuracy"},
    {"name": "Number Of Feeds", "id": "number_of_feeds"},
    {"name": "Staked (Ocean)", "id": "staked_(OCEAN)"},
    {"name": "Gross Income (Ocean)", "id": "gross_income_(OCEAN)"},
    {"name": "Stake Loss (Ocean)", "id": "stake_loss_(OCEAN)"},
    {"name": "Tx Costs (Ocean)", "id": "tx_costs_(OCEAN)"},
    {"name": "Net Income (Ocean)", "id": "net_income_(OCEAN)"},
]


# pylint: disable=too-many-instance-attributes
class AppDataManager:
    def __init__(self, ppss):
        self.lake_dir = ppss.lake_ss.lake_dir
        self.network_name = ppss.web3_pp.network
        self.start_date = None

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

        valid_addresses = [p["user"].lower() for p in self.predictoors_data]
        self.favourite_addresses = [
            addr for addr in ppss.predictoor_ss.my_addresses if addr in valid_addresses
        ]

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
    def _init_feeds_data(self):
        return self._query_db(
            f"""
                SELECT contract, pair, timeframe, source FROM {Prediction.get_lake_table_name()}
                GROUP BY contract, pair, timeframe, source
            """,
        )

    @enforce_types
    def _init_feed_payouts_stats(self):
        query = f"""
                SELECT
                    SPLIT_PART(ID, '-', 1) AS contract,
                    SUM(stake) AS volume,
                    SUM(CASE WHEN payout > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS avg_accuracy,
                    AVG(stake) AS avg_stake
                FROM
                    {Payout.get_lake_table_name()}
            """
        if self.start_date:
            query += f"    WHERE timestamp > {self.start_date}"
        query += """
            GROUP BY
                contract
            ORDER BY volume DESC;
        """
        return self._query_db(query)

    @enforce_types
    def _init_predictoor_payouts_stats(self):
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
        """

        if self.start_date:
            query += f"    WHERE p.timestamp > {self.start_date}"

        query += """
            GROUP BY
                p."user"
            ORDER BY apr DESC;
        """
        return self._query_db(query)

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
        if self.start_date:
            query += f"AND timestamp > {self.start_date}"

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
        if self.start_date:
            query += f"AND timestamp > {self.start_date}"

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

        if self.start_date:
            query += f"WHERE timestamp > {self.start_date}"

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
        """
        if self.start_date:
            query += f" AND timestamp > {self.start_date}"

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
        if self.start_date:
            query_feeds += f"WHERE timestamp > {self.start_date}"
        feeds = self._query_db(
            query_feeds,
            scalar=True,
        )

        query_payouts = f"""
            SELECT
                SUM(CASE WHEN payout > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS avg_accuracy,
                SUM(stake) AS total_stake
            FROM
                {Payout.get_lake_table_name()}
        """
        if self.start_date:
            query_payouts += f"WHERE timestamp > {self.start_date}"
        accuracy, volume = self._query_db(
            query_payouts,
            scalar=True,
        )

        query_subscriptions = f"""
            SELECT COUNT(ID),
            SUM(last_price_value)
            FROM {Subscription.get_lake_table_name()}
        """
        if self.start_date:
            query_subscriptions += f" WHERE timestamp > {self.start_date}"
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
        if self.start_date:
            query_predictions += f" WHERE timestamp > {self.start_date}"
        predictoors = self._query_db(
            query_predictions,
            scalar=True,
        )

        query_payouts = f"""
                SELECT
                    SUM(CASE WHEN payout > 0 THEN 1 ELSE 0 END) * 100 / COUNT(*) AS avg_accuracy,
                    SUM(stake) as tot_stake,
                    SUM(CASE WHEN payout > stake THEN payout - stake ELSE 0 END) AS tot_gross_income
                FROM
                    {Payout.get_lake_table_name()}
            """
        if self.start_date:
            query_payouts += f" WHERE timestamp > {self.start_date}"
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
        self.feeds_cols, self.feeds_table_data, self.raw_feeds_data = (
            self._formatted_data_for_feeds_table
        )

    def refresh_predictoors_data(self):
        self.predictoors_metrics_data = self.predictoors_metrics()
        self.predictoors_data = self._init_predictoor_payouts_stats()

        # data formatting for tables, columns and raw data
        (
            self.predictoors_cols,
            self.predictoors_table_data,
            self.raw_predictoors_data,
        ) = self._formatted_data_for_predictoors_table

    @property
    def _formatted_data_for_feeds_table(
        self,
    ) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]], List[Dict[str, Any]]]:

        new_feed_data = []

        # split the pair column into two columns
        for feed in self.feeds_data:
            split_pair = feed["pair"].split("/")
            feed_item = {}
            feed_item["addr"] = feed["contract"]
            feed_item["base_token"] = split_pair[0]
            feed_item["quote_token"] = split_pair[1]
            feed_item["source"] = feed["source"].capitalize()
            feed_item["timeframe"] = feed["timeframe"]
            feed_item["full_addr"] = feed["contract"]

            result = get_feeds_stat_with_contract(
                feed["contract"], self.feeds_payout_stats
            )

            feed_item.update(result)

            subscription_result = get_feeds_subscription_stat_with_contract(
                feed["contract"], self.feeds_subscriptions
            )

            feed_item.update(subscription_result)

            new_feed_data.append(feed_item)

        columns = get_feed_column_ids(new_feed_data[0])

        formatted_data = format_table(new_feed_data, columns)

        return columns, formatted_data, new_feed_data

    @property
    def _formatted_data_for_predictoors_table(
        self,
    ) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]], List[Dict[str, Any]]]:

        new_predictoor_data = []

        if len(self.predictoors_data) == 0:
            return (
                PREDICTOORS_HOME_PAGE_TABLE_COLS,
                [],
                [],
            )

        # split the pair column into two columns
        for data_item in self.predictoors_data:
            tx_costs = self.fee_cost * float(data_item["stake_count"])

            temp_pred_item = {}
            temp_pred_item["addr"] = str(data_item["user"])
            temp_pred_item["full_addr"] = str(data_item["user"])
            temp_pred_item["apr"] = data_item["apr"]
            temp_pred_item["accuracy"] = data_item["avg_accuracy"]
            temp_pred_item["number_of_feeds"] = str(data_item["feed_count"])
            temp_pred_item["staked_(OCEAN)"] = data_item["total_stake"]
            temp_pred_item["gross_income_(OCEAN)"] = data_item["gross_income"]
            temp_pred_item["stake_loss_(OCEAN)"] = data_item["stake_loss"]
            temp_pred_item["tx_costs_(OCEAN)"] = tx_costs
            temp_pred_item["net_income_(OCEAN)"] = data_item["total_profit"] - tx_costs

            new_predictoor_data.append(temp_pred_item)

        columns = get_feed_column_ids(new_predictoor_data[0])

        formatted_data = format_table(new_predictoor_data, columns)

        return columns, formatted_data, new_predictoor_data

    def filter_for_feeds_table(
        self, predictoor_feeds_only, predictoors_addrs, search_value, selected_feeds
    ):
        filtered_data = self.feeds_data

        # filter feeds by payouts from selected predictoors
        if predictoor_feeds_only and (len(predictoors_addrs) > 0):
            feed_ids = self.feed_ids_based_on_predictoors(
                predictoors_addrs,
            )
            filtered_data = [
                obj
                for obj in filtered_data
                if obj["contract"] in feed_ids
                if obj not in selected_feeds
            ]

        # filter feeds by pair address
        filtered_data = (
            filter_objects_by_field(
                self.feeds_data, "pair", search_value, selected_feeds
            )
            if search_value
            else filtered_data
        )

        return selected_feeds + filtered_data

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

        payout_stats = deepcopy(self.predictoors_data)
        for data in payout_stats:
            formatted_data = format_dict(
                data=data,
                only_include_keys=["user", "total_profit", "avg_accuracy", "avg_stake"],
            )

            new_data = {
                "user_address": formatted_data["user"],
                "total_profit": formatted_data["total_profit"],
                "avg_accuracy": formatted_data["avg_accuracy"],
                "avg_stake": formatted_data["avg_stake"],
                "user": data["user"],
            }

            data.clear()
            data.update(new_data)

        return payout_stats

    @property
    def homepage_feeds_cols(self):
        data = self.feeds_data

        columns = [{"name": col_to_human(col), "id": col} for col in data[0].keys()]
        hidden_columns = ["contract"]

        return (columns, hidden_columns), data

    @property
    def homepage_predictoors_cols(self):
        data = self.formatted_predictoors_home_page_table_data

        columns = [{"name": col_to_human(col), "id": col} for col in data[0].keys()]
        hidden_columns = ["user"]

        if not self.favourite_addresses:
            return (columns, hidden_columns), data

        data = [p for p in data if p["user"] in self.favourite_addresses] + [
            p for p in data if p["user"] not in self.favourite_addresses
        ]

        return (columns, hidden_columns), data
