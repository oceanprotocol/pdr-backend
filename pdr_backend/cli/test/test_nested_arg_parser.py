from enforce_typing import enforce_types

from pdr_backend.cli.nested_arg_parser import (
    NestedArgParser,
    flat_to_nested_args,
)


@enforce_types
def test_nested_arg_parser__initialization():
    parser = NestedArgParser()
    assert parser is not None


@enforce_types
def test_nested_arg_parser__parsing_simple_args():
    parser = NestedArgParser()
    _, nested_args = parser.parse_known_args(["--arg1=value1", "--arg2=value2"])
    assert nested_args["arg1"] == "value1"
    assert nested_args["arg2"] == "value2"


@enforce_types
def test_nested_arg_parser__parsing_nested_args():
    parser = NestedArgParser()
    _, nested_args = parser.parse_known_args(
        ["--nested.arg1=value1", "--nested.arg2=value2"]
    )
    assert nested_args == {"nested": {"arg1": "value1", "arg2": "value2"}}


@enforce_types
def test_nested_arg_parser__different_data_types():
    parser = NestedArgParser()
    _, nested_args = parser.parse_known_args(
        [
            "--config.int=10",
            "--config.float=0.5",
            "--config.names=['name1', 'name2', 42.42, 42]",
        ]
    )
    assert nested_args == {
        "config": {"int": 10, "float": 0.5, "names": ["name1", "name2", 42.42, 42]}
    }

    
@enforce_types
def test_nested_arg_parser__flat_to_nested_args():
    flat_args = {
        "config.int": "10",
        "config.float": "0.5",
        "config.names": "['name1', 'name2', 42.42, 42]",
    }
    nested_args = flat_to_nested_args(flat_args)
    
    assert nested_args == {
        "config": {"int": 10, "float": 0.5, "names": ["name1", "name2", 42.42, 42]}
    }
