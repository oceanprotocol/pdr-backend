from enforce_typing import enforce_types

from pdr_backend.util.point import Point

@enforce_types
def test_point_0():
    p = Point()
    assert str(p) == "{}"
    
@enforce_types
def test_point_1():
    p = Point({"var1":1})
    assert str(p) == "{var1=1}"
    
@enforce_types
def test_point_2():
    p = Point([("var1",1),("var2",2)])
    assert str(p) == "{var1=1, var2=2}"
    
