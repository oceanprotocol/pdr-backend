from typing import Dict

from enforce_typing import enforce_types


class BaseDataStore:
    @enforce_types
    def __new__(cls, base_path: str, read_only: bool = False):
        read_only_key = "0" if read_only is False else "1"
        pattern_key = f"{base_path}_{read_only_key}"

        if not hasattr(cls, "_instances"):
            cls._instances: Dict[str, "BaseDataStore"] = {}

        if pattern_key not in cls._instances:
            instance = super(BaseDataStore, cls).__new__(cls)
            cls._instances[pattern_key] = instance

        return cls._instances[pattern_key]

    @enforce_types
    def __init__(self, base_path: str, read_only: bool = False):
        self.base_path = base_path
        self.read_only = read_only

    @classmethod
    def clear_instances(cls):
        cls._instances = {}
