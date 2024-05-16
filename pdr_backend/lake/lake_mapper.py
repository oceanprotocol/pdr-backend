from abc import ABC, abstractmethod
from collections import OrderedDict
import polars as pl


class LakeMapper(ABC):
    @staticmethod
    @abstractmethod
    def get_lake_schema() -> OrderedDict:
        pass

    @staticmethod
    @abstractmethod
    def get_lake_table_name() -> str:
        pass

    def check_against_schema(self):
        schema = self.get_lake_schema()
        dict_form = self.__dict__

        try:
            pl.DataFrame(dict_form, schema=schema)
        except Exception as e:
            # TODO: how strict do we want to be?
            # Raising an error or just logging some warnings?
            raise ValueError(
                f"Schema error converting {self.__class__} to dataframe: {e}"
            ) from e
