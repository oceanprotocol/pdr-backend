from enforce_typing import enforce_types
import pytest
from pytest import approx

from pdr_backend.sim.calc_pdr_profit import calc_pdr_profit


@enforce_types
def test_calc_pdr_profit__happy_path():
    # true = up, guess = up (correct guess), others fully wrong
    profit = calc_pdr_profit(
        others_stake=2000.0,
        others_accuracy=0.0,
        stake_up=1000.0,
        stake_down=0.0,
        revenue=2.0,
        true_up_close=True,
    )
    assert profit == 2002.0

    # true = down, guess = down (correct guess), others fully wrong
    profit = calc_pdr_profit(
        others_stake=2000.0,
        others_accuracy=0.0,
        stake_up=0.0,
        stake_down=1000.0,
        revenue=2.0,
        true_up_close=False,
    )
    assert profit == 2002.0

    # true = up, guess = down (incorrect guess), others fully right
    profit = calc_pdr_profit(
        others_stake=2000.0,
        others_accuracy=1.0,
        stake_up=0.0,
        stake_down=1000.0,
        revenue=2.0,
        true_up_close=True,
    )
    assert profit == -1000.0

    # true = down, guess = up (incorrect guess), others fully right
    profit = calc_pdr_profit(
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
    profit = calc_pdr_profit(
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
    profit = calc_pdr_profit(
        others_stake=1000.0,
        others_accuracy=0.30,
        stake_up=1000.0,
        stake_down=100.0,
        revenue=2.0,
        true_up_close=True,
    )
    assert profit == approx(516.923)


@enforce_types
def test_calc_pdr_profit__unhappy_path():
    o_stake = 2000.0
    o_accuracy = 0.51
    stake_up = 1000.0
    stake_down = 100.0
    revenue = 15.0
    true_up_close = True

    with pytest.raises(AssertionError):
        calc_pdr_profit(
            -0.1,
            o_accuracy,
            stake_up,
            stake_down,
            revenue,
            true_up_close,
        )

    with pytest.raises(AssertionError):
        calc_pdr_profit(
            o_stake,
            -0.1,
            stake_up,
            stake_down,
            revenue,
            true_up_close,
        )

    with pytest.raises(AssertionError):
        calc_pdr_profit(
            o_stake,
            +1.1,
            stake_up,
            stake_down,
            revenue,
            true_up_close,
        )

    with pytest.raises(AssertionError):
        calc_pdr_profit(
            o_stake,
            o_accuracy,
            -0.1,
            stake_down,
            revenue,
            true_up_close,
        )

    with pytest.raises(AssertionError):
        calc_pdr_profit(
            o_stake,
            o_accuracy,
            stake_up,
            -0.1,
            revenue,
            true_up_close,
        )

    with pytest.raises(AssertionError):
        calc_pdr_profit(
            o_stake,
            o_accuracy,
            stake_up,
            stake_down,
            -0.1,
            true_up_close,
        )
