import os
from pathlib import Path
import pytest

from pdr_backend.util.cache import Cache

TEST_CACHE_DIR = ".test_cache"
TEST_KEY = "test_key"
TEST_VALUE = "test_value"


class TestCache:
    def test_cache_dir_creation(self):
        cache_path = (
            Path(os.path.dirname(os.path.abspath(__file__))).parent / TEST_CACHE_DIR
        )
        assert cache_path.exists()

    def test_save_load(self):
        self.cache_instance.save(TEST_KEY, TEST_VALUE)
        loaded_value = self.cache_instance.load(TEST_KEY)
        assert loaded_value == TEST_VALUE

    def test_load_nonexistent(self):
        result = self.cache_instance.load("nonexistent_key")
        assert result is None

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        # pylint: disable=attribute-defined-outside-init
        self.cache_instance = Cache(cache_dir=TEST_CACHE_DIR)
        yield
        cache_dir_path = (
            Path(os.path.dirname(os.path.abspath(__file__))).parent / TEST_CACHE_DIR
        )
        for item in cache_dir_path.iterdir():
            item.unlink()
        cache_dir_path.rmdir()
