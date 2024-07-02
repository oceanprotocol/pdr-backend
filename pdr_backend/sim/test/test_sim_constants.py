from enforce_typing import enforce_types

from pdr_backend.sim.constants import Dirn, UP, DOWN

@enforce_types
def test_sim_constants():
    assert UP == Dirn.UP
    assert DOWN == Dirn.DOWN

    assert UP in Dirn 
    assert DOWN in Dirn

    assert 1 in Dirn
    assert 2 in Dirn
    assert 0 not in Dirn
    assert 3 not in Dirn
    assert "up" not in Dirn

    assert dirn_str(UP) == "UP"
    assert dirn_str(DOWN) == "DOWN"
    with pytest.raises(ValueError):
        _ = dirn_str(3)
    with pytest.raises(TypeError):
        _ = dirn_str("not an int")
    
    
