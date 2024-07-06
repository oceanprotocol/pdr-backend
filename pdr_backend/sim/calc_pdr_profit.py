from enforce_typing import enforce_types


@enforce_types
def calc_pdr_profit(
    others_stake: float,
    others_accuracy: float,
    stake_up: float,
    stake_down: float,
    revenue: float,
    true_up_close: bool,
) -> float:
    assert others_stake >= 0
    assert 0.0 <= others_accuracy <= 1.0
    assert stake_up >= 0.0
    assert stake_down >= 0.0
    assert revenue >= 0.0

    amt_sent = stake_up + stake_down
    others_stake_correct = others_stake * others_accuracy
    tot_stake = others_stake + stake_up + stake_down
    if true_up_close:
        tot_stake_correct = others_stake_correct + stake_up
        percent_to_me = stake_up / tot_stake_correct
        amt_received = (revenue + tot_stake) * percent_to_me
    else:
        tot_stake_correct = others_stake_correct + stake_down
        percent_to_me = stake_down / tot_stake_correct
        amt_received = (revenue + tot_stake) * percent_to_me
    pdr_profit_OCEAN = amt_received - amt_sent

    return float(pdr_profit_OCEAN)
