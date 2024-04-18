import os

from enforce_typing import enforce_types

from pdr_backend.cli.cli_arguments_lake import str_as_abspath


@enforce_types
@enforce_types
def test_str_as_abspath():
    abs_path = os.path.abspath("lake_data")
    assert str_as_abspath("lake_data") == abs_path
    assert str_as_abspath(os.path.abspath("lake_data")) == abs_path
