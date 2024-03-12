from typing import Dict

from enforce_typing import enforce_types


class BaseDataStore:
    @enforce_types
    def __new__(cls, base_path: str):
        if not hasattr(cls, "_instances"):
            cls._instances: Dict[str, "BaseDataStore"] = {}
        if base_path not in cls._instances:
            instance = super(BaseDataStore, cls).__new__(cls)
            cls._instances[base_path] = instance
        return cls._instances[base_path]

    @enforce_types
    def __init__(self, base_path: str):
        self.base_path = base_path

    @classmethod
    def clear_instances(cls):
        cls._instances = {}
