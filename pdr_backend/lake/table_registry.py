from typing import Optional, Dict, Tuple, List
from polars.type_aliases import SchemaDict
from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import PPSS
from pdr_backend.lake.table import Table


class TableRegistry:
    _instance: Optional["TableRegistry"] = None
    _tables: Dict[str, Table] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TableRegistry, cls).__new__(cls)
        return cls._instance

    @enforce_types
    def register_table(self, table_name: str, table_args: Tuple[str, SchemaDict, PPSS]):
        if table_name in self._tables:
            pass
        self._tables[table_name] = Table(*table_args)
        return self._tables[table_name]

    @enforce_types
    def register_tables(self, tables: Dict[str, Tuple[str, SchemaDict, PPSS]]):
        for table_name, table_args in tables.items():
            self.register_table(table_name, table_args)

    @enforce_types
    def get_table(self, table_name: str):
        return self._tables.get(table_name)

    @enforce_types
    def get_tables(self, table_names: Optional[List] = None):
        if table_names is None:
            table_names = list(self._tables.keys())

        target_tables = [self._tables.get(table_name) for table_name in table_names]

        # do it this way to avoid returning None
        target_tables = [table for table in target_tables if table is not None]

        # do it a dictionary to preserve order
        return dict(zip(table_names, target_tables))

    @enforce_types
    def unregister_table(self, table_name):
        self._tables.pop(table_name, None)
        return True

    @enforce_types
    def clear_tables(self):
        self._tables = {}
        return True
