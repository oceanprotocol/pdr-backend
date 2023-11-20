from pdr_backend.util.listutil import remove_dups

def test_remove_dups():
    assert remove_dups([]) == []
    assert remove_dups([3]) == [3]
    assert remove_dups(["foo"]) == ["foo"]
    assert remove_dups([3,3]) == [3]
    assert remove_dups([3, "foo", "foo", 3, 4, 10, 4, 9]) == [3, "foo", 4, 10, 9]
