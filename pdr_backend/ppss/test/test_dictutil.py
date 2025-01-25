from pdr_backend.util.dictutil import recursive_update


def test_recursive_update():
    initial_dict = {"a": 1, "b": {"c": 2, "d": {"e": 3, "f": 4}}}

    update_dict = {"b": {"c": 5, "d": {"f": 6, "g": 7}, "h": 8}, "i": 9}

    recursive_update(initial_dict, update_dict)

    assert initial_dict == {
        "a": 1,
        "b": {"c": 5, "d": {"e": 3, "f": 6, "g": 7}, "h": 8},
        "i": 9,
    }
