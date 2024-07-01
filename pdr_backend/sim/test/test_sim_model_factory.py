from unittest.mock import Mock

from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import fast_test_yaml_str, PPSS
from pdr_backend.ppss.aimodel_ss import AimodelSS, aimodel_ss_test_dict
from pdr_backend.sim.constants import Dirn, UP, DOWN
from pdr_backend.sim.sim_model import SimModel
from pdr_backend.sim.sim_model_factory import SimModelFactory
from pdr_backend.sim.sim_model_prediction import SimModelPrediction
from pdr_backend.sim.test.resources import get_sim_model_data


@enforce_types
def test_sim_model_factory__attributes():
    f: SimModelFactory = _get_sim_model_factory()
    assert isinstance(f.ppss, PPSS)
    
@enforce_types
def test_sim_model_factory__do_build():
    f: SimModelFactory = _get_sim_model_factory()
    f.aimodel_ss.set_train_every_n_epochs(13)

    # case: no previous model
    assert f.do_build(None, 0)

    # case: have previous model; then on proper iter?
    prev_model = Mock(spec=SimModel)
    assert f.do_build(prev_model, test_i=(13*4)) 
    assert not f.do_build(prev_model, test_i=(13*4+1))

@enforce_types
def test_sim_model_factory__build():
    f: SimModelFactory = _get_sim_model_factory()
    
    data = get_sim_model_data()
    model = f.build(data)
    assert isinstance(model, SimModel)
    
    p = model.predict_next(data)
    assert isinstance(p, SimModelPrediction)
    
@enforce_types
def _get_sim_model_factory() -> SimModelFactory:
    s = fast_test_yaml_str()
    ppss = PPSS(yaml_str=s, network="development")
    return SimModelFactory(ppss)
    
