import argparse
import ast

class NestedArgParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nested_args = {}

    def parse_known_args(self, args=None, namespace=None):
        namespace, remaining_args = super().parse_known_args(args, namespace)

        # process nested args
        for arg in remaining_args:
            if arg.startswith("--"):
                key, eq, value = arg[2:].partition('=')
                if eq:  # Only proceed if '=' is found
                    self._process_nested_arg(key, value)

        return namespace, self.nested_args

    def _process_nested_arg(self, key, value):
        keys = key.split('.')
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
        if '[' in value and ']' in value:
            return ast.literal_eval(value)
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value
