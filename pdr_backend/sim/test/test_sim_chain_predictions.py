import os
from copy import deepcopy
from unittest.mock import patch

import pytest
from enforce_typing import enforce_types


from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.ppss.ppss import PPSS, mock_ppss
from pdr_backend.ppss.predictoor_ss import feedset_test_list
from pdr_backend.sim.sim_chain_predictions import SimChainPredictions
from pdr_backend.sim.sim_engine import SimEngine
from pdr_backend.util.time_types import UnixTimeMs


def mock_gql_update(self):
    ppss = self.ppss

    db = DuckDBDataStore(ppss.lake_ss.lake_dir)
    slots = [
        UnixTimeMs.from_natural_language("1 hour ago").to_seconds(),
        UnixTimeMs.from_natural_language("55 minutes ago").to_seconds(),
        UnixTimeMs.from_natural_language("50 minutes ago").to_seconds(),
        UnixTimeMs.from_natural_language("45 minutes ago").to_seconds(),
    ]

    contract_address = "0xecefd19314ee798921b053694a23974e406da47b"
    # payout_ids id = {contract address}-{slot}-{user}
    payout_ids = [f"{contract_address}-{slot}-0x00" for slot in slots]

    # timestamps are in ms according to slots
    timestamps = [slot * 1000 for slot in slots]

    db.insert_to_table(
        pl.DataFrame(
            {
                "ID": payout_ids,
                "slot": slots,
                "payout": [1, 2, 3, 4],
                "roundSumStakes": [1, 2, 3, 4],
                "roundSumStakesUp": [1, 2, 3, 4],
                "timestamp": timestamps,
            }
        ),
        "pdr_payouts",
    )

    db.insert_to_table(
        pl.DataFrame(
            {
                "timeframe": ["5m"],
                "contract": [contract_address],
                "pair": ["BTC/USDT"],
            }
        ),
        "pdr_predictions",
    )


def _clear_test_db(ppss):
    db = DuckDBDataStore(ppss.lake_ss.lake_dir)
    db.drop_table("pdr_payouts")
    db.drop_table("pdr_predictions")


def mock_gql_init(self, *args):
    # assign args.ppss to self.ppss
    self.ppss = args[0]

    self._update = lambda: mock_gql_update(self)  # Assign the mock update method


@enforce_types
@patch(
    "pdr_backend.sim.sim_chain_predictions.GQLDataFactory.__init__", new=mock_gql_init
)
def test_get_predictions_data(tmpdir):
    s = os.path.abspath("ppss.yaml")
    d = PPSS.constructor_dict(s)

    d["lake_ss"]["lake_dir"] = os.path.join(tmpdir, "lake_data")
    d["lake_ss"]["st_timestr"] = "2 hours ago"
    d["trader_ss"]["feed.timeframe"] = "5m"
    d["sim_ss"]["test_n"] = 20
    ppss = PPSS(d=d, network="sapphire-mainnet")
    feedsets = ppss.predictoor_ss.predict_train_feedsets
    sim_engine = SimEngine(ppss, feedsets[0])

    # Getting prediction dataset
    SimChainPredictions.verify_prediction_data(ppss)

    # check the duckdb file exists in the lake directory
    assert os.path.exists(ppss.lake_ss.lake_dir)
    assert os.path.exists(os.path.join(ppss.lake_ss.lake_dir, "duckdb.db"))

    st_ut_s = UnixTimeMs(ppss.lake_ss.st_timestamp).to_seconds()
    prediction_dataset = SimChainPredictions.get_predictions_data(
        st_ut_s,
        UnixTimeMs(ppss.lake_ss.fin_timestamp).to_seconds(),
        ppss,
        sim_engine.predict_feed,
    )

    db = DuckDBDataStore(ppss.lake_ss.lake_dir)
    test_query = f"""
            SELECT 
                slot
            FROM pdr_payouts
            WHERE
                slot > {st_ut_s}
            LIMIT 1"""

    df = db.query_data(test_query)
    assert df is not None
    assert isinstance(prediction_dataset, dict)

    assert df["slot"][0] in prediction_dataset
    _clear_test_db(ppss)


@patch(
    "pdr_backend.sim.sim_chain_predictions.GQLDataFactory.__init__", new=mock_gql_init
)
def test_verify_prediction_data():
    s = os.path.abspath("ppss.yaml")
    d = PPSS.constructor_dict(s)
    path = "my_lake_data"

    d["lake_ss"]["lake_dir"] = path
    d["lake_ss"]["st_timestr"] = "2 hours ago"
    d["trader_ss"]["feed.timeframe"] = "5m"
    d["sim_ss"]["test_n"] = 10
    ppss = PPSS(d=d, network="sapphire-mainnet")
    resp = SimChainPredictions.verify_prediction_data(ppss)
    assert resp is True
    _clear_test_db(ppss)


@enforce_types
def test_verify_use_chain_data_in_syms_dependencies():
    # create ppss
    ppss = mock_ppss(
        feedset_test_list(),
        "sapphire-mainnet",
    )

    # baseline should pass
    ppss.verify_use_chain_data_in_syms_dependencies()

    # modify lake time and number of epochs to simulate so the verification fails
    ppss2 = deepcopy(ppss)
    ppss2.sim_ss.d["test_n"] = 1000
    ppss2.lake_ss.d["st_timestr"] = "2 hours ago"
    with pytest.raises(ValueError):
        ppss2.verify_use_chain_data_in_syms_dependencies()
