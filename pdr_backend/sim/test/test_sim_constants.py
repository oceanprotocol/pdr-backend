from enforce_typing import enforce_types

from pdr_backend.sim.constants import Dirn, UP, DOWN

@enforce_types
def test_sim_constants():
    assert UP == Dirn.UP
    assert DOWN == Dirn.DOWN

    assert UP in Dirn 
    assert DOWN in Dirn

    assert UP == 1
    assert DOWN == 2
    assert 0 not in Dirn
    assert 3 not in Dirn
    assert "up" not in Dirn
    
    
