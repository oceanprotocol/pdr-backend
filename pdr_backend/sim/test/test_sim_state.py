from enforce_typing import enforce_types
import numpy as np
import pytest
from pytest import approx

from pdr_backend.aimodel.true_vs_pred import PERF_NAMES, TrueVsPred
from pdr_backend.sim.constants import Dirn, dirn_str, UP, DOWN
from pdr_backend.sim.sim_state import (
    HistPerfs,
    HistProfits,
    PROFIT_NAMES,
    SimState,
)

# =============================================================================
# test HistPerfs


@enforce_types
@pytest.mark.parametrize("dirn", [UP, DOWN])
def test_hist_perfs__basic_init(dirn):
    # set data
    dirn_s = dirn_str(dirn)
    hist_perfs = HistPerfs(dirn)

    # test empty raw state
    assert hist_perfs.acc_ests == hist_perfs.acc_ls == hist_perfs.acc_us == []
    assert hist_perfs.f1s == hist_perfs.precisions == hist_perfs.recalls == []
    assert hist_perfs.losses == []

    # test names
    assert len(PERF_NAMES) == 7
    target_names = _target_perfs_names(dirn_s)
    assert hist_perfs.metrics_names_instance() == target_names
    assert hist_perfs.metrics_names_instance()[0] == f"acc_est_{dirn_s}"
    assert hist_perfs.metrics_names_instance()[-1] == f"loss_{dirn_s}"
    assert HistPerfs.metrics_names_static(dirn) == target_names

    # test can't call for metrics
    assert not hist_perfs.have_data()
    with pytest.raises(AssertionError):
        _ = hist_perfs.recent_metrics_values()
    with pytest.raises(AssertionError):
        _ = hist_perfs.final_metrics_values()


@enforce_types
@pytest.mark.parametrize("dirn", [UP, DOWN])
def test_hist_perfs__main(dirn):
    # set data
    dirn_s = dirn_str(dirn)
    target_names = [f"{name}_{dirn_s}" for name in PERF_NAMES]
    hist_perfs = HistPerfs(dirn)

    perfs_list1 = list(np.arange(0.1, 7.1, 1.0))  # 0.1, 1.1, ..., 6.1
    perfs_list2 = list(np.arange(0.2, 7.2, 1.0))  # 0.2, 1.2, ..., 6.2
    hist_perfs.update(perfs_list1)
    hist_perfs.update(perfs_list2)

    # test raw state
    assert hist_perfs.acc_ests == [0.1, 0.2]
    assert hist_perfs.acc_ls == [1.1, 1.2]
    assert hist_perfs.acc_us == [2.1, 2.2]
    assert hist_perfs.f1s == [3.1, 3.2]
    assert hist_perfs.precisions == [4.1, 4.2]
    assert hist_perfs.recalls == [5.1, 5.2]
    assert hist_perfs.losses == [6.1, 6.2]

    # test can call for metrics
    assert hist_perfs.have_data()

    # test *recent* metrics
    values = hist_perfs.recent_metrics_values()
    assert len(values) == 7
    assert sorted(values.keys()) == sorted(target_names)
    assert f"acc_est_{dirn_s}" in values.keys()
    assert values == {
        f"acc_est_{dirn_s}": 0.2,
        f"acc_l_{dirn_s}": 1.2,
        f"acc_u_{dirn_s}": 2.2,
        f"f1_{dirn_s}": 3.2,
        f"precision_{dirn_s}": 4.2,
        f"recall_{dirn_s}": 5.2,
        f"loss_{dirn_s}": 6.2,
    }

    # test *final* metrics
    values = hist_perfs.final_metrics_values()
    assert len(values) == 7
    assert sorted(values.keys()) == sorted(target_names)
    assert f"acc_est_{dirn_s}" in values.keys()
    assert values == {
        f"acc_est_{dirn_s}": 0.2,
        f"acc_l_{dirn_s}": 1.2,
        f"acc_u_{dirn_s}": 2.2,
        f"f1_{dirn_s}": np.mean([3.1, 3.2]),
        f"precision_{dirn_s}": np.mean([4.1, 4.2]),
        f"recall_{dirn_s}": np.mean([5.1, 5.2]),
        f"loss_{dirn_s}": np.mean([6.1, 6.2]),
    }


@enforce_types
def _target_perfs_names(dirn_s: str):
    return [f"{name}_{dirn_s}" for name in PERF_NAMES]


# =============================================================================
# test HistProfits


@enforce_types
def test_hist_profits__basic_init():
    # set data
    hist_profits = HistProfits()

    # test empty raw data
    assert hist_profits.pdr_profits_OCEAN == []
    assert hist_profits.trader_profits_USD == []

    # test names
    target_names = PROFIT_NAMES
    names = HistProfits.metrics_names()
    assert names == target_names

    # test can't call for metrics
    assert not hist_profits.have_data()
    with pytest.raises(AssertionError):
        _ = hist_profits.recent_metrics_values()
    with pytest.raises(AssertionError):
        _ = hist_profits.final_metrics_values()


@enforce_types
def test_hist_profits__update():
    # set data
    hist_profits = HistProfits()
    hist_profits.update(2.1, 3.1)
    hist_profits.update(2.2, 3.2)

    # test raw values
    assert hist_profits.pdr_profits_OCEAN == [2.1, 2.2]
    assert hist_profits.trader_profits_USD == [3.1, 3.2]

    # test can call for metrics
    assert hist_profits.have_data()

    # test *recent* metrics
    target_names = PROFIT_NAMES
    values = hist_profits.recent_metrics_values()
    assert sorted(values.keys()) == sorted(target_names)
    assert values == {"pdr_profit_OCEAN": 2.2, "trader_profit_USD": 3.2}

    # test *final* metrics
    values = hist_profits.final_metrics_values()
    assert sorted(values.keys()) == sorted(target_names)
    assert values == {
        "pdr_profit_OCEAN": np.sum([2.1, 2.2]),
        "trader_profit_USD": np.sum([3.1, 3.2]),
    }


@enforce_types
def test_hist_profits__calc_pdr_profit():
    # true = up, guess = up (correct guess), others fully wrong
    profit = HistProfits.calc_pdr_profit(
        others_stake=2000.0,
        others_accuracy=0.0,
        stake_up=1000.0,
        stake_down=0.0,
        revenue=2.0,
        true_up_close=True,
    )
    assert profit == 2002.0

    # true = down, guess = down (correct guess), others fully wrong
    profit = HistProfits.calc_pdr_profit(
        others_stake=2000.0,
        others_accuracy=0.0,
        stake_up=0.0,
        stake_down=1000.0,
        revenue=2.0,
        true_up_close=False,
    )
    assert profit == 2002.0

    # true = up, guess = down (incorrect guess), others fully right
    profit = HistProfits.calc_pdr_profit(
        others_stake=2000.0,
        others_accuracy=1.0,
        stake_up=0.0,
        stake_down=1000.0,
        revenue=2.0,
        true_up_close=True,
    )
    assert profit == -1000.0

    # true = down, guess = up (incorrect guess), others fully right
    profit = HistProfits.calc_pdr_profit(
        others_stake=2000.0,
        others_accuracy=1.0,
        stake_up=1000.0,
        stake_down=0.0,
        revenue=2.0,
        true_up_close=False,
    )
    assert profit == -1000.0

    # true = up, guess = up AND down (half-correct), others fully wrong
    # summary: I should get back all my stake $, plus stake $ of others
    # calculations:
    # - sent (by me) = stake_up + stake_down = 1000 + 100 = 1100
    # - tot_stake (by all) = others_stake + stake_up + stake_down
    #   = 1000 + 1000 + 100 = 2100
    # - tot_stake_correct (by all) = others_stake_correct + stake_up
    #   = 1000*0.0 + 1000 = 1000
    # - percent_to_me = stake_up / tot_stake_correct = 1000/1000 = 1.0
    # - rec'd (to me) = (revenue + tot_stake) * percent_to_me
    #   = (2 + 3100) * 1.0 = 3102
    # - profit = received - sent = 2102 - 1100 = 1002
    profit = HistProfits.calc_pdr_profit(
        others_stake=1000.0,
        others_accuracy=0.00,
        stake_up=1000.0,
        stake_down=100.0,
        revenue=2.0,
        true_up_close=True,
    )
    assert profit == 1002.0

    # true = up, guess = lots up & some down, others 30% accurate
    # summary: <not simple, however I should come out ahead>
    # calculations:
    # - amt_sent = stake_up + stake_down = 1000 + 100 = 1100
    # - others_stake_correct = 1000 * 0.3 = 300
    # - tot_stake = others_stake + stake_up + stake_down
    #   = 1000 + 1000 + 100 = 2100
    # - tot_stake_correct = others_stake_correct + stake_up
    #   = 1000*0.30 + 1000 = 300 + 1000 = 1300
    # - percent_to_me = stake_up / tot_stake_correct
    #   = 1000/1300 = 0.7692307692307693
    # - amt_received = (revenue + tot_stake) * percent_to_me
    #   = (2 + 2100) * 0.769230 = 1616.9230769
    # - profit = received - sent = 1616.9230769 - 1100 = 516.923
    profit = HistProfits.calc_pdr_profit(
        others_stake=1000.0,
        others_accuracy=0.30,
        stake_up=1000.0,
        stake_down=100.0,
        revenue=2.0,
        true_up_close=True,
    )
    assert profit == approx(516.923)


@enforce_types
def test_hist_profits__calc_pdr_profit__unhappy_path():
    o_stake = 2000.0
    o_accuracy = 0.51
    stake_up = 1000.0
    stake_down = 100.0
    revenue = 15.0
    true_up_close = True

    with pytest.raises(AssertionError):
        HistProfits.calc_pdr_profit(
            -0.1,
            o_accuracy,
            stake_up,
            stake_down,
            revenue,
            true_up_close,
        )

    with pytest.raises(AssertionError):
        HistProfits.calc_pdr_profit(
            o_stake,
            -0.1,
            stake_up,
            stake_down,
            revenue,
            true_up_close,
        )

    with pytest.raises(AssertionError):
        HistProfits.calc_pdr_profit(
            o_stake,
            +1.1,
            stake_up,
            stake_down,
            revenue,
            true_up_close,
        )

    with pytest.raises(AssertionError):
        HistProfits.calc_pdr_profit(
            o_stake,
            o_accuracy,
            -0.1,
            stake_down,
            revenue,
            true_up_close,
        )

    with pytest.raises(AssertionError):
        HistProfits.calc_pdr_profit(
            o_stake,
            o_accuracy,
            stake_up,
            -0.1,
            revenue,
            true_up_close,
        )

    with pytest.raises(AssertionError):
        HistProfits.calc_pdr_profit(
            o_stake,
            o_accuracy,
            stake_up,
            stake_down,
            -0.1,
            true_up_close,
        )


# =============================================================================
# test SimState


@enforce_types
def test_sim_state__basic_init():
    # set data
    st = SimState()

    # test empty raw state
    assert st.iter_number == 0
    assert st.sim_model_data is None
    assert st.sim_model is None
    assert isinstance(st.true_vs_pred[UP], TrueVsPred)
    assert isinstance(st.true_vs_pred[DOWN], TrueVsPred)
    assert isinstance(st.hist_perfs[UP], HistPerfs)
    assert isinstance(st.hist_perfs[DOWN], HistPerfs)
    assert isinstance(st.hist_profits, HistProfits)

    # test names
    target_names = _target_state_names()
    assert len(target_names) == 7 * 2 + 2
    names = SimState.metrics_names()
    assert names == target_names

    # test can't call for metrics
    assert not st.have_data()
    with pytest.raises(AssertionError):
        _ = st.recent_metrics_values()
    with pytest.raises(AssertionError):
        _ = st.final_metrics_values()


@enforce_types
def test_sim_state__init_loop_attributes():
    # init
    st = SimState()

    # change after init
    st.iter_number = 1
    st.sim_model = "foo"

    # should go back to init state
    st.init_loop_attributes()

    # check
    assert st.iter_number == 0
    assert st.sim_model is None


@enforce_types
def test_sim_state__main():
    st = SimState()
    target_names = _target_state_names()

    # update
    trueval = {UP: True, DOWN: False}
    predprob = {UP: 0.6, DOWN: 0.3}

    st.update(trueval, predprob, pdr_profit_OCEAN=1.4, trader_profit_USD=1.5)
    st.update(trueval, predprob, pdr_profit_OCEAN=2.4, trader_profit_USD=2.5)

    # test raw state -- true_vs_pred
    assert st.true_vs_pred[UP].truevals == [True, True]
    assert st.true_vs_pred[UP].predprobs == [0.6, 0.6]
    assert st.true_vs_pred[DOWN].truevals == [False, False]
    assert st.true_vs_pred[DOWN].predprobs == [0.3, 0.3]

    # test *recent* metrics
    values = st.recent_metrics_values()
    assert len(values) == 7 * 2 + 2
    assert sorted(values.keys()) == sorted(target_names)
    for name, val in values.items():
        if name == "pdr_profit_OCEAN":
            assert val == 2.4
        elif name == "trader_profit_USD":
            assert val == 2.5
        elif "loss" in name:
            assert 0.0 <= val <= 3.0
        else:  # hist_perfs value
            assert 0.0 <= val <= 1.0, (name, val)

    # test *final* metrics
    values = st.final_metrics_values()
    assert sorted(values.keys()) == sorted(target_names)
    for name, val in values.items():
        if name == "pdr_profit_OCEAN":
            assert val == np.sum([1.4, 2.4])
        elif name == "trader_profit_USD":
            assert val == np.sum([1.5, 2.5])
        elif "loss" in name:
            assert 0.0 <= val <= 3.0
        else:  # hist_perfs value
            assert 0.0 <= val <= 1.0, (name, val)


@enforce_types
def _target_state_names():
    return [
        f"{name}_{dirn_str(dirn)}" for dirn in [UP, DOWN] for name in PERF_NAMES
    ] + PROFIT_NAMES
