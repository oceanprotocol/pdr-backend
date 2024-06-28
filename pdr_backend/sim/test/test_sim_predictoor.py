from enforce_typing import enforce_types

from pdr_backend.ppss.predictoor_ss import PredictoorSS, predictoor_ss_test_dict
from pdr_backend.sim.sim_predictoor import SimPredictoor

@enforce_types
def test_sim_pdr__attributes():
    sim_pdr = _sim_pdr()
    assert isinstance(sim_pdr.pdr_ss, PredictoorSS)

    
@enforce_types
def test_sim_pdr__properties():
    sim_pdr = _sim_pdr()
    max_stake_amt = cls.pdr_ss.stake_amount.amt_eth
    assert isinstance(max_stake_amt, float)
    assert max_stake_amt > 0.0

    
@enforce_types
def test_sim_pdr__predict_iter():
    # base data
    sim_pdr = _sim_pdr()

    # case 1: don't trust models
    stake_up, stake_down = sim_pdr.predict_iter(False, False, 0.4, 0.6)
    assert stake_up == stake_down == 0.0

    # case 2: UP dominates
    stake_up, stake_down = sim_pdr.predict_iter(True, False, 0.6, 0.4)
    assert 0.0 < stake_down < stake_up < 1.0
    assert (stake_up + stake_down) <= sim_pdr.max_stake_amt
    
    # case 3: DOWN dominates
    stake_up, stake_down = sim_pdr.predict_iter(False, True, 0.4, 0.6)
    assert 0.0 < stake_up < stake_down < 1.0
    assert (stake_up + stake_down) <= sim_pdr.max_stake_amt
    
                                   
@enforce_types
def _sim_pdr() -> SimPredictoor:
    pdr_d = predictoor_ss_test_dict()
    pdr_ss = PredictoorSS(pdr_d)
    sim_pdr = SimPredictoor(pdr_ss)
    return sim_pdr
    
