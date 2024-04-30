import pytest
from pdr_backend.predictoor.util import find_shared_slots


def test_shared_slots_basic():
    pending_slots = {"addr1": [1, 2, 3, 4], "addr2": [1, 2, 3, 4, 5], "addr3": [2]}
    expected = [
        (["addr1", "addr2"], [1, 3, 4]),
        (["addr1", "addr2", "addr3"], [2]),
        (["addr2"], [5]),
    ]
    assert find_shared_slots(pending_slots) == expected


def test_no_shared_slots():
    pending_slots = {
        "addr1": [1, 2],
        "addr2": [3, 4],
    }
    expected = [
        (["addr1"], [1, 2]),
        (["addr2"], [3, 4]),
    ]
    assert find_shared_slots(pending_slots) == expected


def test_single_address_multiple_slots():
    pending_slots = {"addr1": [1, 2, 3]}
    expected = [
        (["addr1"], [1, 2, 3]),
    ]
    assert find_shared_slots(pending_slots) == expected


def test_empty_input():
    pending_slots = {}
    expected = []
    assert find_shared_slots(pending_slots) == expected
