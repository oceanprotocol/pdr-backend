import os
import pickle
from pathlib import Path


class Cache:
    def __init__(self, cache_dir=".cache"):
        self.app_path = Path(os.path.dirname(os.path.abspath(__file__)))
        self.cache_path = self.app_path / cache_dir

        if not self.cache_path.exists():
            self.cache_path.mkdir()
            print("Created dir")

    def save(self, key, value):
        file_path = self.cache_path / f"{key}.pkl"
        with open(file_path, "wb") as file:
            pickle.dump(value, file)

    def load(self, key):
        file_path = self.cache_path / f"{key}.pkl"
        if file_path.exists():
            with open(file_path, "rb") as file:
                return pickle.load(file)
        return None
