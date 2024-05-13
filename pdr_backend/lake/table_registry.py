from typing import Dict, List, Optional

from enforce_typing import enforce_types

from pdr_backend.lake.table import Table
from pdr_backend.ppss.ppss import PPSS


class TableRegistry:
    _instance: Optional["TableRegistry"] = None
    _tables: Dict[str, Table] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TableRegistry, cls).__new__(cls)
        return cls._instance

    @enforce_types
    def register_table(self, dataclass: type, ppss: PPSS):
        table_name = dataclass.get_lake_table_name()  # type: ignore[attr-defined]
        if table_name in self._tables:
            pass
        self._tables[table_name] = Table(dataclass, ppss)
        return self._tables[table_name]

    @enforce_types
    def register_tables(self, dataclasses: List[type], ppss: PPSS):
        for dataclass in dataclasses:
            self.register_table(dataclass, ppss)

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
