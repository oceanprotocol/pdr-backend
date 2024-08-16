import re
from typing import List, Union

from enforce_typing import enforce_types

# dollar Bar
class ArgDB:
    def __init__(self, db_str: str):
        """
        @arguments
          db_str -- e.g. "db_2100.5"
        """
        if not re.match(r"db_\d+(\.\d+)?$", db_str):
            raise ValueError("dollar threshold must start with 'tb_' + int")

        _, value_str = _unpack_db_str(db_str)
        try:
            float(value_str)
        except ValueError:
            raise ValueError(f"Invalid float value: '{value_str}'")

        self.db_str = db_str

    def __eq__(self, other):
        return self.db_str == str(other)

    def __str__(self):
        return self.db_str

    def threshold(self) -> float:
        return float(self.db_str.split("_")[1])


class ArgDBs(List[ArgDB]):
    def __init__(self, dollar_thresholds: Union[List[str], List[ArgDB]]):
        if not isinstance(dollar_thresholds, list):
            raise TypeError("dollar_thresholds must be a list")

        dbs = []
        for db in dollar_thresholds:
            db = ArgDB(db) if isinstance(db, str) else db
            dbs.append(db)

        super().__init__(dbs)

    @staticmethod
    def from_str(dollar_thresholds_str: str):
        """
        @description
          Parses a comma-separated string of dollar_thresholds, e.g. "db-105,db-200"
        """
        if not isinstance(dollar_thresholds_str, str):
            raise TypeError("dollar_thresholds_str must be a string")

        return ArgDBs(dollar_thresholds_str.split(","))

    def __str__(self):
        if not self:
            return ""

        return ",".join([str(db) for db in self])


@enforce_types
def db_str_ok(s: str) -> bool:
    try:
        ArgDBs.from_str(s)
        return True
    except ValueError:
        return False


@enforce_types
def verify_db_str(s: str):
    """Raise an error if input string is invalid."""
    _ = ArgDB(s)


@enforce_types
def verify_dbs_str(s: str):
    """Raise an error if input string is invalid."""
    _ = ArgDBs.from_str(s)


def _unpack_db_str(db_str: str) -> tuple:
    """
    Unpacks the tb_str into prefix and value_str.

    Example: Given 'db_2100.5'
    Return ('db', '2100.5')
    """
    prefix, value_str = db_str.split("_", 1)
    return (prefix, value_str)
