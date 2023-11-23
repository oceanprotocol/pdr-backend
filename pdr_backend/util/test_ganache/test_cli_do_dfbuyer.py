import os

import argparse

from unittest.mock import patch
from enforce_typing import enforce_types

from pdr_backend.util.cli_module import do_dfbuyer


@enforce_types
@patch("pdr_backend.dfbuyer.dfbuyer_agent.wait_until_subgraph_syncs")
def test_main(monkeypatch):
    class MockArgs(argparse.Namespace):
        @property
        def NETWORK(self):
            return "development"

        @property
        def YAML_FILE(self):
            return os.path.abspath("ppss.yaml")

    class MockArgParser:
        def __init__(self, *args, **kwargs):
            pass

        def parse_args(self):
            return MockArgs()

    monkeypatch.setattr(
        "pdr_backend.util.cli_module.DfbuyerArgParser",
        MockArgParser,
    )

    do_dfbuyer()
