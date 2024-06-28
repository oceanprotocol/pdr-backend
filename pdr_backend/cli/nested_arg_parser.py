#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import argparse
import ast

from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import PPSS


@enforce_types
class NestedArgParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nested_args = {}

    def parse_known_args(self, args=None, namespace=None):
        namespace, remaining_args = super().parse_known_args(args, namespace)

        # process nested args
        for arg in remaining_args:
            if arg.startswith("--"):
                key, eq, value = arg[2:].partition("=")
                if eq:  # Only proceed if '=' is found
                    self._process_nested_arg(key, value)

        if hasattr(namespace, "PPSS_FILE") and hasattr(namespace, "NETWORK"):
            namespace.PPSS = PPSS(
                yaml_filename=namespace.PPSS_FILE,
                network=namespace.NETWORK,
                nested_override_args=self.nested_args,
            )

        return namespace, self.nested_args

    def _process_nested_arg(self, key, value):
        keys = key.split(".")
        current_dict = self.nested_args

        for i, k in enumerate(keys):
            if i == len(keys) - 1:
                # last key, set the value
                current_dict[k] = self._convert_value(value)
                break
            # keep nesting
            if k not in current_dict:
                current_dict[k] = {}
            current_dict = current_dict[k]

    def _convert_value(self, value):
        if "[" in value and "]" in value:
            return ast.literal_eval(value)
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value


@enforce_types
def flat_to_nested_args(flat_args: dict) -> dict:
    """
    @description
       Given a point, construct nested_args dict.
       The nested_args can then be applied to the ppss construction dict.

    @arguments
       flat_args -- dict of [dot-separated-varname] : var_value

    @return
      nested_args - dict of dict of ...

    @notes
      Implemented by 'hacking' nested_arg_parser
    """
    args_list = [f"--{key}={val}" for key, val in flat_args.items()]
    parser = NestedArgParser()
    _, nested_args = parser.parse_known_args(args_list)
    return nested_args
