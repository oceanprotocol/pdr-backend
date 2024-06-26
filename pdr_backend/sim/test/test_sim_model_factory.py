from enforce_typing import enforce_types

from pdr_backend.sim.sim_model import SimModel
from pdr_backend.sim.test.resources import get_sim_model_data

from pdr_backend.ppss.aimodel_ss import AimodelSS, aimodel_ss_test_dict
from pdr_backend.sim.constants import Dirn, UP, DOWN
from pdr_backend.sim.sim_model import SimModel
from pdr_backend.sim.sim_model_prediction import SimModelPrediction


@enforce_types
def test_sim_model_factory__attributes():
    f: SimModelFactory = _get_sim_model_factory()
    assert isinstance(f.aimodel_ss, AimodelSS)
    
@enforce_types
def test_sim_model_factory__do_build():
    f: SimModelFactory = _get_sim_model_factory()

    # case: no previous model
    assert f.do_build(None, 0)

    # case: have previous model; then on proper iter?
    prev_model = Mock()
    assert f.do_build(prev_model, test_i=3) 
    assert not f.do_build(prev_model, test_i=4)

@enforce_types
def test_sim_model_factory__build():
    f: SimModelFactory = _get_sim_model_factory()
    
    sim_model_data = get_sim_model_data()
    model = f.do_build(sim_model_data)
    assert isinstance(model, SimModel)
    
    p = model.predict_next(d)
    assert isinstance(p, SimModelPrediction)
    
@enforce_types
def _get_sim_model_factory() -> SimModelFactory:
    aimodel_ss = _get_aimodel_ss()
    return SimModelFactory(aimodel_ss)
    
@enforce_types
def _get_aimodel_ss() -> AimodelSS:
    d = aimodel_ss_test_dict()
    return AimodelSS(d)
