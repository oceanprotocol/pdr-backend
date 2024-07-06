from enforce_typing import enforce_types

from pdr_backend.ppss.predictoor_ss import PredictoorSS, predictoor_ss_test_dict
from pdr_backend.binmodel.binmodel_prediction import BinmodelPrediction
from pdr_backend.sim.sim_predictoor import SimPredictoor


@enforce_types
def test_sim_predictoor__attributes():
    sim_pdr = _sim_pdr()
    assert isinstance(sim_pdr.pdr_ss, PredictoorSS)


@enforce_types
def test_sim_predictoor__properties():
    sim_pdr = _sim_pdr()
    max_stake_amt = sim_pdr.pdr_ss.stake_amount.amt_eth
    assert isinstance(max_stake_amt, float | int)
    assert max_stake_amt > 0.0


@enforce_types
def test_sim_predictoor__predict_iter():
    # base data
    sim_pdr = _sim_pdr()

    # case 1: don't trust models
    p = BinmodelPrediction(conf_thr=0.9, prob_UP=0.4, prob_DOWN=0.4)
    assert not p.do_trust_models()
    stake_up, stake_down = sim_pdr.predict_iter(p)
    assert stake_up == stake_down == 0.0

    # case 2: UP dominates
    p = BinmodelPrediction(conf_thr=0.1, prob_UP=0.6, prob_DOWN=0.4)
    assert p.do_trust_models()
    stake_up, stake_down = sim_pdr.predict_iter(p)
    assert 0.0 < stake_down < stake_up < 1.0
    assert (stake_up + stake_down) <= sim_pdr.max_stake_amt

    # case 3: DOWN dominates
    p = BinmodelPrediction(conf_thr=0.1, prob_UP=0.4, prob_DOWN=0.6)
    assert p.do_trust_models()
    stake_up, stake_down = sim_pdr.predict_iter(p)
    assert 0.0 < stake_up < stake_down < 1.0
    assert (stake_up + stake_down) <= sim_pdr.max_stake_amt


@enforce_types
def _sim_pdr() -> SimPredictoor:
    pdr_d = predictoor_ss_test_dict()
    pdr_ss = PredictoorSS(pdr_d)
    sim_pdr = SimPredictoor(pdr_ss)
    return sim_pdr
