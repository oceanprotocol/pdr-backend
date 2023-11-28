import os
from os import getenv

import argparse

from enforce_typing import enforce_types

from pdr_backend.util.cli_module import do_dfbuyer


@enforce_types
def test_main(monkeypatch):
    class MockArgs(argparse.Namespace):
        @property
        def NETWORK(self):
            return getenv("NETWORK_OVERRIDE") or "development"  # allow override

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

    class MockAgent:
        was_run = False

        def __init__(self, ppss):
            pass

        def run(self):
            self.__class__.was_run = True

    monkeypatch.setattr(
        "pdr_backend.util.cli_module.DFBuyerAgent",
        MockAgent,
    )

    do_dfbuyer()

    assert MockAgent.was_run
