from pdr_backend.cli.nested_arg_parser import NestedArgParser

def test_initialization():
    parser = NestedArgParser()
    assert parser is not None

def test_parsing_simple_args():
    parser = NestedArgParser()
    _, nested_args = parser.parse_known_args(['--arg1=value1', '--arg2=value2'])
    assert nested_args["arg1"] == 'value1'
    assert nested_args["arg2"] == 'value2'

def test_parsing_nested_args():
    parser = NestedArgParser()
    _, nested_args = parser.parse_known_args(['--nested.arg1=value1', '--nested.arg2=value2'])
    assert nested_args == {'nested': {'arg1': 'value1', 'arg2': 'value2'}}

def test_different_data_types():
    parser = NestedArgParser()
    _, nested_args = parser.parse_known_args(['--config.int=10', '--config.float=0.5', '--config.names=[\'name1\', \'name2\', 42.42, 42]'])
    assert nested_args == {'config': {'int': 10, 'float': 0.5, 'names': ['name1', 'name2', 42.42, 42]}}