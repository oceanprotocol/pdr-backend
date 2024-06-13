from typing import List, Dict

import polars as pl
from enforce_typing import enforce_types


@enforce_types
def _object_list_to_df(objects: List[object], schema: Dict) -> pl.DataFrame:
    """
    @description
        Convert list objects to a dataframe using their __dict__ structure.
    """
    # Get all predictions into a dataframe
    obj_dicts = [object.__dict__ for object in objects]
    obj_df = pl.DataFrame(obj_dicts, schema=schema, orient="row")
    assert obj_df.schema == schema

    return obj_df
