import logging

from datetime import datetime, timedelta
from typing import Union, List, Dict, Any, Optional
from enforce_typing import enforce_types
import dash
from web3 import Web3

from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.payout import Payout
from pdr_backend.lake.prediction import Prediction
from pdr_backend.util.currency_types import Eth, Wei

logger = logging.getLogger("predictoor_dashboard_utils")


@enforce_types
def _query_db(lake_dir: str, query: str) -> Union[List[dict], Exception]:
    """
    Query the database with the given query.
    Args:
        lake_dir (str): Path to the lake directory.
        query (str): SQL query.
    Returns:
        dict: Query result.
    """
    try:
        db = DuckDBDataStore(lake_dir, read_only=True)
        df = db.query_data(query)
        db.duckdb_conn.close()
        return df.to_dicts() if len(df) else []
    except Exception as e:
        logger.error("Error querying the database: %s", e)
        return []


@enforce_types
def get_feeds_data_from_db(lake_dir: str):
    return _query_db(
        lake_dir,
        f"""
            SELECT contract, pair, timeframe, source FROM {Prediction.get_lake_table_name()}
            GROUP BY contract, pair, timeframe, source
        """,
    )


@enforce_types
def get_predictoors_data_from_db(lake_dir: str):
    return _query_db(
        lake_dir,
        f"""
            SELECT user FROM {Prediction.get_lake_table_name()}
            GROUP BY user
        """,
    )


@enforce_types
def get_user_payouts_stats_from_db(lake_dir: str):
    return _query_db(
        lake_dir,
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


def get_feed_ids_based_on_predictoors_from_db(
    lake_dir: str, predictoor_addrs: List[str]
):
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
    return _query_db(lake_dir, query)[0]["feed_addrs"]


@enforce_types
def get_payouts_from_db(
    feed_addrs: List[str], predictoor_addrs: List[str], start_date: int, lake_dir: str
) -> List[dict]:
    """
    Get payouts data for the given feed and predictoor addresses.
    Args:
        feed_addrs (list): List of feed addresses.
        predictoor_addrs (list): List of predictoor addresses.
        lake_dir (str): Path to the lake directory.
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

    return _query_db(lake_dir, query)


@enforce_types
def filter_objects_by_field(
    objects: List[Dict[str, Any]],
    field: str,
    search_string: str,
    previous_objects: Optional[List] = None,
) -> List[Dict[str, Any]]:
    if previous_objects is None:
        previous_objects = []

    return [
        obj
        for obj in objects
        if search_string.lower() in obj[field].lower() and obj not in previous_objects
    ]


@enforce_types
def select_or_clear_all_by_table(
    ctx,
    table_id: str,
    rows: List[Dict[str, Any]],
) -> Union[List[int], dash.no_update]:
    """
    Select or unselect all rows in a table.
    Args:
        ctx (dash.callback_context): Dash callback context.
    Returns:
        list: List of selected rows or dash.no_update.
    """
    if not ctx.triggered:
        return dash.no_update

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    selected_rows = []
    if button_id == f"select-all-{table_id}":
        selected_rows = list(range(len(rows)))

    return selected_rows


@enforce_types
def get_predictoors_data_from_payouts(
    user_payout_stats: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Process the user payouts stats data.
    Args:
        user_payout_stats (list): List of user payouts stats data.
    Returns:
        list: List of processed user payouts stats data.
    """

    for data in user_payout_stats:
        new_data = {
            "user_address": data["user"][:5] + "..." + data["user"][-5:],
            "total_profit": round(data["total_profit"], 2),
            "avg_accuracy": round(data["avg_accuracy"], 2),
            "avg_stake": round(data["avg_stake"], 2),
            "user": data["user"],
        }

        data.clear()
        data.update(new_data)

    return user_payout_stats


def get_start_date_from_period(period: int):
    return int((datetime.now() - timedelta(days=period)).timestamp())


def get_date_period_text(payouts: List):
    if not payouts:
        return "there is no data available"
    start_date = payouts[0]["slot"] if len(payouts) > 0 else 0
    end_date = payouts[-1]["slot"] if len(payouts) > 0 else 0
    date_period_text = f"""
        available {datetime.fromtimestamp(start_date).strftime('%d-%m-%Y')}
        - {datetime.fromtimestamp(end_date).strftime('%d-%m-%Y')}
    """
    return date_period_text


def calculate_tx_gass_fee_cost_in_OCEAN(web3_pp, feed_contract_addr, prices):
    web3 = Web3(Web3.HTTPProvider(web3_pp.rpc_url))

    # generic params
    predicted_value = True
    stake_amt_wei = Eth(10).to_wei().amt_wei
    prediction_ts = Eth(1721723066).to_wei().amt_wei
    # predictoor_addr = "0xe2DD09d719Da89e5a3D0F2549c7E24566e947260"

    # gas price
    gas_price = web3.eth.gas_price

    # gas amount
    contract = web3.eth.contract(
        address=web3.to_checksum_address(feed_contract_addr),
        abi=web3_pp.get_contract_abi("ERC20Template3"),
    )
    gas_estimate_prediction = contract.functions["submitPredval"](
        predicted_value, stake_amt_wei, prediction_ts
    ).estimate_gas({"from": "0xe2DD09d719Da89e5a3D0F2549c7E24566e947260"})

    # cals tx fee cost
    tx_fee_rose_prediction = (
        Wei(gas_estimate_prediction * gas_price).to_eth().amt_eth / 10
    )

    tx_fee_price_usdt_prediction = tx_fee_rose_prediction * prices["ROSE"]
    tx_fee_price_ocean_prediction = tx_fee_price_usdt_prediction / prices["OCEAN"]

    # gas_estimate_payout = contract.functions["payout"](
    #    prediction_ts, predictoor_addr
    # ).estimate_gas({"from": "0xe2DD09d719Da89e5a3D0F2549c7E24566e947260"})
    # tx_fee_rose_payout = Wei(gas_estimate_payout * gas_price).to_eth().amt_eth
    # tx_fee_price_usdt_payout = tx_fee_rose_payout * prices["ROSE"]
    # tx_fee_price_ocean_payout = tx_fee_price_usdt_payout / prices["OCEAN"]
    # print(tx_fee_price_ocean_prediction, tx_fee_price_ocean_payout)

    return tx_fee_price_ocean_prediction
