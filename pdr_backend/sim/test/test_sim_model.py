from enforce_typing import enforce_types

from pdr_backend.sim.sim_model import SimModel
from pdr_backend.sim.test.resources import get_sim_model_data

@enforce_types
def test_sim_model():
    model_UP = Mock(foo)
    model_DOWN = Mock(foo)
    model = SimModel(ppss, model_UP, model_DOWN)
    p = model.predict_next(d)
    
