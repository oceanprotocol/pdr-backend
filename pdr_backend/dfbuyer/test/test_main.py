import pytest

from pdr_backend.dfbuyer.main import numbers_with_sum


class TestNumbersWithSum:
    def test_basic(self):
        result = numbers_with_sum(3, 6)
        assert len(result) == 3
        assert sum(result) == 6

    def test_empty_list(self):
        assert numbers_with_sum(-1, 10) == []
        assert numbers_with_sum(5, 3) == []
        assert numbers_with_sum(0, 0) == []

    def test_single_number(self):
        assert numbers_with_sum(1, 5) == [5]
        assert numbers_with_sum(1, 1) == [1]

    def test_sum_lesser_than_numbers(self):
        assert numbers_with_sum(10, 5) == []

    def test_large_numbers(self):
        result = numbers_with_sum(1000, 500500)
        assert len(result) == 1000
        assert sum(result) == 500500

    def test_fuzz(self):
        total_tests = 1000
        passed_tests = 0
        for _ in range(total_tests):
            result = numbers_with_sum(5, 20)
            if len(result) == 5 and sum(result) == 20:
                passed_tests += 1
        assert passed_tests == total_tests

    @pytest.mark.parametrize(
        "n, k, expected_length, expected_sum",
        [(5, 15, 5, 15), (3, 9, 3, 9), (4, 7, 4, 7), (2, 11, 2, 11)],
    )
    def test_parametrize(self, n, k, expected_length, expected_sum):
        result = numbers_with_sum(n, k)
        assert len(result) == expected_length
        assert sum(result) == expected_sum
