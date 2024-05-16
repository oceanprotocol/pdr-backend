from abc import ABC, abstractmethod
from collections import OrderedDict


class LakeMapper(ABC):
    @staticmethod
    @abstractmethod
    def get_lake_schema() -> OrderedDict:
        pass

    @staticmethod
    @abstractmethod
    def get_lake_table_name() -> str:
        pass
