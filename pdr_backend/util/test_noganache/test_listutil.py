from collections import OrderedDict

from enforce_typing import enforce_types

from pdr_backend.util.listutil import obj_in_objlist, remove_dups


@enforce_types
def test_remove_dups():
    assert remove_dups([]) == []
    assert remove_dups([3]) == [3]
    assert remove_dups(["foo"]) == ["foo"]
    assert remove_dups([3, 3]) == [3]
    assert remove_dups([3, "foo", "foo", 3, 4, 10, 4, 9]) == [3, "foo", 4, 10, 9]

@enforce_types
def test_obj_in_objlist__dict():
    assert not obj_in_objlist({}, [])
    assert obj_in_objlist({}, [{}])
    assert not obj_in_objlist({"a": 1}, [])
    assert not obj_in_objlist({}, [{"a": 1}])
    
    assert obj_in_objlist({"a": 1}, [{"a": 1}])
    assert not obj_in_objlist({"a": 1}, [{"b": 2}])
    
    assert obj_in_objlist({"a": 1}, [{"a": 1}, {"b": 2}])
    assert obj_in_objlist({"a": 1}, [{"b": 2}, {"a": 1}])

    assert not obj_in_objlist({"b": 1}, [{"a": 1}])
    assert not obj_in_objlist({"a": 2}, [{"a": 1}])
    

@enforce_types
def test_obj_in_objlist__OrderedDict():
    assert not obj_in_objlist(OrderedDict(), [])
    assert obj_in_objlist(OrderedDict(), [OrderedDict()])
    assert not obj_in_objlist(OrderedDict({"a": 1}), [])
    assert not obj_in_objlist(OrderedDict(), [OrderedDict({"a": 1})])
    
    assert obj_in_objlist(OrderedDict({"a": 1}), [OrderedDict({"a": 1})])
    assert not obj_in_objlist(OrderedDict({"a": 1}), [OrderedDict({"b": 2})])
    
    assert obj_in_objlist(
        OrderedDict({"a": 1}), [OrderedDict({"a": 1}), OrderedDict({"b": 2})]
    )
    assert obj_in_objlist(
        OrderedDict({"a": 1}), [OrderedDict({"b": 2}), OrderedDict({"a": 1})]
    )

    assert not obj_in_objlist(OrderedDict({"b": 1}), [OrderedDict({"a": 1})])
    assert not obj_in_objlist(OrderedDict({"a": 2}), [OrderedDict({"a": 1})])
    
