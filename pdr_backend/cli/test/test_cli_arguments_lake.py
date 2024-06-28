#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os
from unittest.mock import patch
import pytest

from enforce_typing import enforce_types

from pdr_backend.cli.cli_arguments_lake import str_as_abspath
from pdr_backend.cli.cli_module_lake import do_lake_subcommand


@enforce_types
def test_str_as_abspath():
    abs_path = os.path.abspath("lake_data")
    assert str_as_abspath("lake_data") == abs_path
    assert str_as_abspath(os.path.abspath("lake_data")) == abs_path


def test_timestr_args():
    args = ["raw", "update", "ppss.yaml", "sapphire-mainnet"]

    with patch("pdr_backend.cli.cli_module_lake.do_lake_raw_update") as raw_update:
        do_lake_subcommand(args)

    assert raw_update.called
