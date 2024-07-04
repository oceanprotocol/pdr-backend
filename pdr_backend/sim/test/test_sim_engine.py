#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os
import shutil
from unittest.mock import patch

import pytest
import polars as pl
from dash import Dash
from enforce_typing import enforce_types
from selenium.common.exceptions import NoSuchElementException  # type: ignore[import-untyped]

from pdr_backend.aimodel.aimodel import Aimodel
from pdr_backend.cli.predict_train_feedsets import PredictTrainFeedsets
from pdr_backend.ppss.lake_ss import LakeSS, lake_ss_test_dict
from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str
from pdr_backend.ppss.predictoor_ss import PredictoorSS, predictoor_ss_test_dict
from pdr_backend.ppss.sim_ss import SimSS, sim_ss_test_dict
from pdr_backend.sim.dash_plots.callbacks import get_callbacks
from pdr_backend.sim.dash_plots.view_elements import get_layout
from pdr_backend.sim.sim_engine import SimEngine
from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.util.time_types import UnixTimeMs


@enforce_types
# pylint: disable=unused-argument
def test_sim_engine(tmpdir, check_chromedriver, dash_duo):
    s = fast_test_yaml_str(tmpdir)
    ppss = PPSS(yaml_str=s, network="development")

    # set feeds; we'll use them below
    feedset_list = [
        {
            "predict": "binanceus BTC/USDT c 5m",
            "train_on": "binanceus BTC/USDT c 5m",
        }
    ]
    feedsets = PredictTrainFeedsets.from_list_of_dict(feedset_list)

    # lake ss
    lake_dir = os.path.join(tmpdir, "parquet_data")
    d = lake_ss_test_dict(lake_dir, feeds=feedsets.feed_strs)
    assert "st_timestr" in d
    d["st_timestr"] = "2023-06-18"
    d["fin_timestr"] = "2023-06-19"
    ppss.lake_ss = LakeSS(d)

    # predictoor ss
    d = predictoor_ss_test_dict(feedset_list)
    assert "max_n_train" in d["aimodel_data_ss"]
    assert "autoregressive_n" in d["aimodel_data_ss"]
    assert "approach" in d["aimodel_ss"]
    assert "train_every_n_epochs" in d["aimodel_ss"]
    d["aimodel_data_ss"]["max_n_train"] = 20
    d["aimodel_data_ss"]["autoregressive_n"] = 1
    d["aimodel_ss"]["approach"] = "ClassifLinearRidge"
    d["aimodel_ss"]["train_every_n_epochs"] = 2
    ppss.predictoor_ss = PredictoorSS(d)

    # sim ss
    log_dir = os.path.join(tmpdir, "logs")
    d = sim_ss_test_dict(log_dir, True, test_n=5)
    ppss.sim_ss = SimSS(d)

    # go
    feedsets = ppss.predictoor_ss.predict_train_feedsets
    sim_engine = SimEngine(ppss, feedsets[0])

    assert sim_engine.model is None
    sim_engine.run()
    assert isinstance(sim_engine.model, Aimodel)

    app = Dash("pdr_backend.sim.sim_dash")
    app.config["suppress_callback_exceptions"] = True
    app.run_id = sim_engine.multi_id
    app.layout = get_layout()
    get_callbacks(app)

    dash_duo.start_server(app)
    dash_duo.wait_for_text_to_equal(
        "#sim_state_text", f"Simulation ID: {sim_engine.multi_id}", timeout=100
    )

    # default visibility: shows figure from first tab
    dash_duo.find_element("#pdr_profit_vs_time")

    # does not show figures from other tabs
    with pytest.raises(NoSuchElementException):
        dash_duo.find_element("#trader_profit_vs_time")

    with pytest.raises(NoSuchElementException):
        dash_duo.find_element("#model_performance_vs_time")

    tabs = {
        "predictor_profit_tab": ["pdr_profit_vs_time", "pdr_profit_vs_ptrue"],
        "trader_profit_tab": ["trader_profit_vs_time", "trader_profit_vs_ptrue"],
        "model_performance_tab": ["model_performance_vs_time"],
        "model_response_tab": ["aimodel_response", "aimodel_varimps"],
        "model_residuals_tab": ["prediction_residuals_other"],
    }

    for tab_name, figures in tabs.items():
        # when tab is clicked, it shows its figures
        tab = dash_duo.find_element(f".{tab_name}")
        tab.click()
        assert "tab--selected" in tab.get_attribute("class")
        for figure_name in figures:
            dash_duo.find_element(f"#{figure_name}")


def _clear_test_db(ppss):
    db = DuckDBDataStore(ppss.lake_ss.lake_dir)
    db.drop_table("pdr_payouts")
    db.drop_table("pdr_predictions")


def mock_gql_init(self, *args):
    # assign args.ppss to self.ppss
    self.ppss = args[0]

    self._update = lambda: mock_gql_update(self)  # Assign the mock update method


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


@enforce_types
@patch("pdr_backend.sim.sim_engine.GQLDataFactory.__init__", new=mock_gql_init)
def test_get_predictions_signals_data(tmpdir):
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
    sim_engine._get_past_predictions_from_chain(ppss)

    # check the duckdb file exists in the lake directory
    assert os.path.exists(ppss.lake_ss.lake_dir)
    assert os.path.exists(os.path.join(ppss.lake_ss.lake_dir, "duckdb.db"))

    st_ut_s = UnixTimeMs(ppss.lake_ss.st_timestamp).to_seconds()
    prediction_dataset = sim_engine._get_predictions_signals_data(
        st_ut_s,
        UnixTimeMs(ppss.lake_ss.fin_timestamp).to_seconds(),
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


@patch("pdr_backend.sim.sim_engine.GQLDataFactory.__init__", new=mock_gql_init)
def test_get_past_predictions_from_chain():
    s = os.path.abspath("ppss.yaml")
    d = PPSS.constructor_dict(s)
    path = "my_lake_data"

    d["lake_ss"]["lake_dir"] = path
    d["lake_ss"]["st_timestr"] = "2 hours ago"
    d["trader_ss"]["feed.timeframe"] = "5m"
    d["sim_ss"]["test_n"] = 1000
    ppss = PPSS(d=d, network="sapphire-mainnet")
    feedsets = ppss.predictoor_ss.predict_train_feedsets
    sim_engine = SimEngine(ppss, feedsets[0])

    # run with wrong ppss lake config so there is not enough data fetched
    resp = sim_engine._get_past_predictions_from_chain(ppss)
    assert resp is False

    # run with right ppss lake config
    if os.path.exists(path):
        shutil.rmtree(path)

    # needs to be inspected and fixed
    d["sim_ss"]["test_n"] = 10
    ppss = PPSS(d=d, network="sapphire-mainnet")

    sim_engine = SimEngine(ppss, feedsets[0])
    resp = sim_engine._get_past_predictions_from_chain(ppss)
    assert resp is True
    _clear_test_db(ppss)
