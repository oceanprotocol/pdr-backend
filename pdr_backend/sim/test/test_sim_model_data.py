from enforce_typing import enforce_types
import numpy as np
from numpy.testing import assert_array_equal

from pdr_backend.sim.constants import Dirn, UP, DOWN
from pdr_backend.sim.sim_model_data import SimModelData, SimModelData1Dir
from pdr_backend.sim.test.resources import get_Xy_UP, get_Xy_DOWN

@enforce_types
def test_sim_model_data_1dir():
    # build data
    (X_UP, ytrue_UP) = get_Xy_UP()
        
    assert X_UP.shape == (4,2)
    assert ytrue_UP.shape == (4,)
    ytrue_UP_train = ytrue_UP[:3]
    data_UP = SimModelData1Dir(X_UP, ytrue_UP, ["x0", "x1"])
    
    # basic tests
    assert_array_equal(X_UP, data_UP.X)
    assert_array_equal(ytrue_UP, data_UP.ytrue)
    assert data_UP.colnames == ["x0", "x1"]

    # test properties
    assert data_UP.st == 0
    assert data_UP.fin == (4 - 1) == 3
    assert_array_equal(data_UP.X_train, X_UP[0:3,:])
    assert_array_equal(data_UP.X_test, X_UP[3:3+1,:])
    assert_array_equal(data_UP.ytrue_train, ytrue_UP_train)

    
@enforce_types
def test_sim_model_data_both_dirs():
    # build data
    (X_UP, ytrue_UP) = get_Xy_UP()
    (X_DOWN, ytrue_DOWN) = get_Xy_DOWN()
    colnames_UP = ["x0_high", "x1_high"]
    colnames_DOWN = ["x0_low", "x1_low"]

    data_UP = SimModelData1Dir(X_UP, ytrue_UP, colnames_UP)
    data_DOWN = SimModelData1Dir(X_DOWN, ytrue_DOWN, colnames_DOWN)
    data = SimModelData(data_UP, data_DOWN)

    # basic tests
    assert UP in data
    assert DOWN in data
    for key in data:
        assert isinstance(key, Dirn)
    assert isinstance(data[UP], SimModelData1Dir)
    assert isinstance(data[DOWN], SimModelData1Dir)
    
    assert_array_equal(X_UP, data[UP].X)
    assert_array_equal(ytrue_UP, data[UP].ytrue)
    
    assert_array_equal(X_DOWN, data[DOWN].X)
    assert_array_equal(ytrue_DOWN, data[DOWN].ytrue)

    assert sorted(data.X_test.keys()) == [UP, DOWN]
    assert_array_equal(data.X_test[UP], data[UP].X_test)
    assert_array_equal(data.X_test[DOWN], data[DOWN].X_test)

    
