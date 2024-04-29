# pylint: disable=redefined-outer-name
from unittest.mock import MagicMock, Mock, patch

import pytest
import numpy as np
import polars as pl

from enforce_typing import enforce_types
from numpy.testing import assert_array_equal

from pdr_backend.cli.predict_train_feedsets import PredictTrainFeedset
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.ppss.predictoor_ss import PredictoorSS
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.predictoor.predictoor_agent import PredictoorAgent
from pdr_backend.predictoor.test.mockutil import (
    INIT_TIMESTAMP,
    INIT_BLOCK_NUMBER,
    mock_ppss_1feed,
    mock_ppss_2feeds,
)
from pdr_backend.util.currency_types import Eth
from pdr_backend.subgraph.subgraph_feed import SubgraphFeed

# ===========================================================================
# test approach {1, 2, 3} - main loop

# do _not_ parameterize these. It's much easier to test them individually
#  and debug when they're separate


@enforce_types
def test_predictoor_agent_main1(tmpdir, monkeypatch, pred_submitter_mgr):
    _test_predictoor_agent_main(1, str(tmpdir), monkeypatch, pred_submitter_mgr)


@enforce_types
def test_predictoor_agent_main2(tmpdir, monkeypatch, pred_submitter_mgr):
    _test_predictoor_agent_main(2, str(tmpdir), monkeypatch, pred_submitter_mgr)


def test_predictoor_agent_main3(tmpdir, monkeypatch, pred_submitter_mgr):
    _test_predictoor_agent_main(3, str(tmpdir), monkeypatch, pred_submitter_mgr)


@pytest.fixture()
def pred_submitter_mgr():
    with patch("pdr_backend.predictoor.predictoor_agent.PredSubmitterMgr") as mock:
        mock.submit_prediction.return_value = {"transactionHash": b"hello", "status": 1}
        mock.contract_address = "0x123"
        yield mock


@enforce_types
def _test_predictoor_agent_main(
    approach: int, tmpdir: str, monkeypatch, pred_submitter_mgr
):
    """
    @description
        Run the agent for a while, and then do some basic sanity checks.
        Uses get_agent_1feed, *not* 2feeds.
    """
    assert approach in [1, 2, 3]

    # mock tokens
    mock_token = Mock()
    mock_token.balanceOf.return_value = Eth(1000).to_wei()

    with patch("pdr_backend.ppss.web3_pp.Token", return_value=mock_token), patch(
        "pdr_backend.ppss.web3_pp.NativeToken", return_value=mock_token
    ):
        _, ppss, _mock_pdr_contract = mock_ppss_1feed(
            approach,
            tmpdir,
            monkeypatch,
        )
        assert ppss.predictoor_ss.approach == approach
        ppss.predictoor_ss.d["bot_only"]["pred_submitter_mgr"] = pred_submitter_mgr.contract_address
        feed_contracts = ppss.web3_pp.query_feed_contracts()
        web3_config = ppss.web3_pp.web3_config
        w3 = ppss.web3_pp.w3
        mock_token = Mock()
        mock_token.balanceOf.return_value = Eth(1000).to_wei()
        ppss.web3_pp = MagicMock(spec=Web3PP)
        ppss.web3_pp.OCEAN_Token = mock_token
        ppss.web3_pp.NativeToken = mock_token
        ppss.web3_pp.get_single_contract.return_value = _mock_pdr_contract
        ppss.web3_pp.query_feed_contracts.return_value = feed_contracts
        ppss.web3_pp.web3_config = web3_config
        ppss.web3_pp.w3 = w3
        # now we're done the mocking, time for the real work!!

        # real work: main iterations
        agent = PredictoorAgent(ppss)
        for _ in range(500):
            agent.take_step()

    # log some final results for debubbing / inspection
    mock_w3 = ppss.web3_pp.web3_config.w3
    print("\n" + "/" * 160)
    print("Done iterations")
    print(
        f"init block_number = {INIT_BLOCK_NUMBER}"
        f", final = {mock_w3.eth.block_number}"
    )
    print()
    print(f"init timestamp = {INIT_TIMESTAMP}, final = {mock_w3.eth.timestamp}")
    print(f"all timestamps seen = {mock_w3.eth._timestamps_seen}")
    print()
    print(
        "unique prediction_slots = "
        f"{sorted(set(_mock_pdr_contract._prediction_slots))}"
    )
    print(f"all prediction_slots = {_mock_pdr_contract._prediction_slots}")

    # relatively basic sanity tests
    # TO-DO Use the Prediction Submitter Manager to check these, commented out for now
    # assert _mock_pdr_contract._prediction_slots
    # assert (mock_w3.eth.timestamp + 2 * ppss.predictoor_ss.timeframe_s) >= max(
    #     _mock_pdr_contract._prediction_slots
    # )


# ===========================================================================
# test constructor


@enforce_types
def test_predictoor_agent_init_empty(pred_submitter_mgr):
    """
    @description
      Basic test: when there's no feeds, does it complain?
    """
    # test with no feeds
    pred_submitter_mgr_addr = pred_submitter_mgr.contract_address
    mock_ppss_empty = MagicMock(spec=PPSS)
    mock_ppss_empty.predictoor_ss = MagicMock(spec=PredictoorSS)
    mock_ppss_empty.predictoor_ss.get_feed_from_candidates.return_value = []
    mock_ppss_empty.predictoor_ss.pred_submitter_mgr = pred_submitter_mgr_addr
    mock_ppss_empty.web3_pp = MagicMock(spec=Web3PP)
    mock_ppss_empty.web3_pp.query_feed_contracts.return_value = {}

    with pytest.raises(ValueError, match="No feeds found"):
        PredictoorAgent(mock_ppss_empty)


# ===========================================================================
# test approach 3 - get_prediction()

BTC_CLOSE_VALS = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0]
ETH_CLOSE_VALS = [30.0, 31.0, 32.0, 33.0, 34.0, 35.0, 36.0, 37.0, 38.0, 39.0]


def mock_get_ohlcv_data2(*args, **kwargs):  # pylint: disable=unused-argument
    d = {
        "timestamp": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
        "binanceus:BTC/USDT:open": [1.0] * 10,
        "binanceus:BTC/USDT:high": [1.0] * 10,
        "binanceus:BTC/USDT:low": [1.0] * 10,
        "binanceus:BTC/USDT:close": BTC_CLOSE_VALS,
        "binanceus:BTC/USDT:volume": [1.0] * 10,
        "binanceus:ETH/USDT:open": [1.0] * 10,
        "binanceus:ETH/USDT:high": [1.0] * 10,
        "binanceus:ETH/USDT:low": [1.0] * 10,
        "binanceus:ETH/USDT:close": ETH_CLOSE_VALS,
        "binanceus:ETH/USDT:volume": [1.0] * 10,
    }
    mergedohlcv_df = pl.DataFrame(d)
    return mergedohlcv_df


class MockModel:
    """scikit-learn style model"""

    def __init__(self):
        self.aimodel_ss = None  # fill this in later, after patch applied
        self.last_X = None  # for tracking test results
        self.last_yptrue = None  # ""

    def predict_ptrue(self, X: np.ndarray) -> np.ndarray:
        (n_points, _) = X.shape
        assert n_points == 1  # this mock can only handle 1 input point

        CLOSE_VALS = X
        prob_up = np.sum(CLOSE_VALS) / 1e6
        assert 0.0 <= prob_up <= 1.0
        yptrue = np.array([prob_up])

        self.last_X, self.last_yptrue = X, yptrue  # cache for testing
        return yptrue


@enforce_types
def test_predictoor_agent_calc_stakes2_1feed(tmpdir, monkeypatch, pred_submitter_mgr):
    """
    @description
      Test calc_stakes2() on 1 feed.

      Approach to test:
      - mergedohlcv_df has simple pre-set values: CLOSE_VALS
      - prob_up = model.predict_ptrue(X) is a simple sum of X-values
      - then, test that sum(CLOSE_VALS[-ar_n:])/1e6 == prob_up
        - where ar_n = autoregressive_n = 3
        - where the /1e6 is so 0 <= prob_up <= 1.0 when summing BTC prices
    """
    mock_model = MockModel()

    def mock_build(*args, **kwargs):  # pylint: disable=unused-argument
        return mock_model

    d = "pdr_backend.predictoor.predictoor_agent"
    with patch(f"{d}.PredictoorAgent.get_ohlcv_data", mock_get_ohlcv_data2), patch(
        f"{d}.AimodelFactory.build", mock_build
    ):

        # initialize agent
        _, ppss, _ = mock_ppss_1feed(
            2, str(tmpdir), monkeypatch, pred_submitter_mgr.contract_address
        )
        aimodel_ss = ppss.predictoor_ss.aimodel_ss

        # do prediction
        mock_model.aimodel_ss = aimodel_ss

        feed_contracts = ppss.web3_pp.query_feed_contracts()
        ppss.web3_pp = Mock(spec=Web3PP)
        ppss.web3_pp.query_feed_contracts.return_value = feed_contracts

        agent = PredictoorAgent(ppss)
        feed = ppss.predictoor_ss.predict_train_feedsets[0]
        agent.calc_stakes2(feed)

        ar_n = aimodel_ss.autoregressive_n
        assert ar_n == 3

        assert mock_model.last_X.shape == (1, 3) == (1, ar_n * 1)
        expected_X = np.array([BTC_CLOSE_VALS[-ar_n:]])  # [17.0, 18.0, 19.0]
        expected_prob_up = sum(BTC_CLOSE_VALS[-ar_n:]) / 1e6
        expected_yptrue = np.array([expected_prob_up])

        assert_array_equal(expected_X, mock_model.last_X)
        assert_array_equal(expected_yptrue, mock_model.last_yptrue)


@enforce_types
def test_predictoor_agent_calc_stakes2_2feeds(tmpdir, monkeypatch, pred_submitter_mgr):
    """
    @description
      Test calc_stakes2(), when X has >1 input feed
    """
    mock_model = MockModel()

    def mock_build(*args, **kwargs):  # pylint: disable=unused-argument
        return mock_model

    d = "pdr_backend.predictoor.predictoor_agent"
    with patch(f"{d}.PredictoorAgent.get_ohlcv_data", mock_get_ohlcv_data2), patch(
        f"{d}.AimodelFactory.build", mock_build
    ):

        # initialize agent
        feeds, ppss = mock_ppss_2feeds(
            2, str(tmpdir), monkeypatch, pred_submitter_mgr.contract_address
        )
        assert ppss.predictoor_ss.approach == 2
        feed_contracts = ppss.web3_pp.query_feed_contracts()
        ppss.web3_pp = Mock(spec=Web3PP)
        ppss.web3_pp.query_feed_contracts.return_value = feed_contracts

        assert len(feeds) == 2
        aimodel_ss = ppss.predictoor_ss.aimodel_ss

        # do prediction
        mock_model.aimodel_ss = aimodel_ss
        agent = PredictoorAgent(ppss)
        feed = ppss.predictoor_ss.predict_train_feedsets[0]
        agent.calc_stakes2(feed)

        ar_n = aimodel_ss.autoregressive_n
        assert ar_n == 3

        assert mock_model.last_X.shape == (1, 6) == (1, ar_n * 2)

        # [17.0, 18.0, 19.0, 37.0, 38.0, 39.0]
        expected_X = np.array([BTC_CLOSE_VALS[-ar_n:] + ETH_CLOSE_VALS[-ar_n:]])

        expected_prob_up = sum(BTC_CLOSE_VALS[-ar_n:] + ETH_CLOSE_VALS[-ar_n:]) / 1e6
        expected_yptrue = np.array([expected_prob_up])

        assert_array_equal(expected_X, mock_model.last_X)
        assert_array_equal(expected_yptrue, mock_model.last_yptrue)


@enforce_types
@pytest.mark.parametrize(
    "OCEAN, ROSE, expected",
    [
        (
            Eth(100).to_wei(),
            Eth(2).to_wei(),
            True,
        ),  # All balances are sufficient
        (
            Eth(0).to_wei(),
            Eth(2).to_wei(),
            False,
        ),  # OCEAN balance too low
        (
            Eth(100).to_wei(),
            Eth(0).to_wei(),
            False,
        ),  # ROSE balance too low
        (
            Eth(0).to_wei(),
            Eth(0).to_wei(),
            False,
        ),  # Both balances too low
    ],
)
def test_balance_check(tmpdir, monkeypatch, OCEAN, ROSE, expected, pred_submitter_mgr):
    mock_model = MockModel()
    _, ppss = mock_ppss_2feeds(
        2, str(tmpdir), monkeypatch, pred_submitter_mgr.contract_address
    )
    aimodel_ss = ppss.predictoor_ss.aimodel_ss

    mock_model.aimodel_ss = aimodel_ss

    feed_contracts = ppss.web3_pp.query_feed_contracts()
    mock_OCEAN = Mock()
    mock_OCEAN.balanceOf.return_value = OCEAN
    mock_ROSE = Mock()
    mock_ROSE.balanceOf.return_value = ROSE
    ppss.web3_pp = Mock(spec=Web3PP)
    ppss.web3_pp.OCEAN_Token = mock_OCEAN
    ppss.web3_pp.NativeToken = mock_ROSE
    ppss.web3_pp.query_feed_contracts.return_value = feed_contracts

    agent = PredictoorAgent(ppss)

    assert agent.check_balances(Eth(100)) == expected


def test_calc_stakes_across_feeds(tmpdir, monkeypatch):
    _, ppss, _mock_pdr_contract = mock_ppss_1feed(
        1,
        str(tmpdir),
        monkeypatch,
    )
    feed_contracts = ppss.web3_pp.query_feed_contracts()
    predictoor_ss = ppss.predictoor_ss
    predictoor_ss.d["bot_only"]["pred_submitter_mgr"] = "0x1"
    predictoor_ss.d["stake_amount"] = 1.0
    predictoor_ss.d["bot_only"]["s_until_epoch_end"] = 50000
    web3_config = ppss.web3_pp.web3_config
    w3 = ppss.web3_pp.w3

    contract_mock = Mock()
    contract_mock.get_current_epoch.return_value = 30
    ppss.web3_pp.get_single_contract = Mock()
    ppss.web3_pp.get_single_contract.return_value = contract_mock

    feeds = [
        SubgraphFeed("BTC/USDT 5m", "0x1", "", 300, 0, "", "", "5m", ""),
        SubgraphFeed("BTC/USDT 1h", "0x2", "", 3600, 0, "", "", "1h", ""),
    ]
    predict_train_feedsets = [
        PredictTrainFeedset.from_dict(
            {
                "predict": "binance BTC/USDT o 5m",
                "train_on": "binance BTC/USDT ETH/USDT o 5m",
            }
        ),
        PredictTrainFeedset.from_dict(
            {
                "predict": "binance LTC/USDT o 1h",
                "train_on": "binance LTC/USDT ADA/USDT o 1h",
            }
        ),
    ]
    predictoor_ss.get_predict_train_feedset = Mock()
    predictoor_ss.get_predict_train_feedset.side_effect = predict_train_feedsets

    ppss = MagicMock(spec=PPSS)
    ppss.predictoor_ss = predictoor_ss
    ppss.web3_pp = MagicMock(spec=Web3PP)
    ppss.web3_pp.get_single_contract.return_value = _mock_pdr_contract
    ppss.web3_pp.query_feed_contracts.return_value = feed_contracts
    ppss.web3_pp.web3_config = web3_config
    ppss.web3_pp.w3 = w3
    with patch("pdr_backend.predictoor.predictoor_agent.PredSubmitterMgr"):
        agent = PredictoorAgent(ppss=ppss)

    stakes = agent.calc_stakes_across_feeds(feeds)
    assert 600 in stakes.slots, "Must have a prediction for next 5m slot"
    assert 7200 in stakes.slots, "Must have a prediction for next 1h slot"

    target_slots = stakes.target_slots
    preds_5m = target_slots[600]
    assert preds_5m[0].feed == feeds[0], "Must have a prediction for BTC/USDT 5m"
    assert preds_5m[0].stake_up + preds_5m[0].stake_down == Eth(1.0), "sum up to 1.0"

    preds_1h = target_slots[7200]
    assert preds_1h[0].feed == feeds[1], "Must have a prediction for BTC/USDT 1h"
    assert preds_1h[0].stake_up + preds_1h[0].stake_down == Eth(1.0), "sum up to 1.0"
