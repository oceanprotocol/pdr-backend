import pytest

from pdr_backend.cli.cli_arguments import (
    CustomArgParser,
    defined_parsers,
    do_help_long,
    get_arg_parser,
    print_args,
)


def test_arg_parser():
    for arg in defined_parsers:
        if arg == "do_deployer":
            # deployer uses subparsers, not compatible with CustomArgParser
            continue
        parser = get_arg_parser(arg)
        assert isinstance(parser, CustomArgParser)

    with pytest.raises(ValueError):
        get_arg_parser("xyz")


def test_do_help_long(capfd):
    with pytest.raises(SystemExit):
        do_help_long()

    out, _ = capfd.readouterr()
    assert "Predictoor tool" in out
    assert "Main tools:" in out


def test_print_args(caplog):
    SimArgParser = defined_parsers["do_sim"]
    parser = SimArgParser
    args = ["sim", "ppss.yaml"]
    parsed_args = parser.parse_args(args)

    print_args(parsed_args)

    assert "pdr sim: Begin" in caplog.text
    assert "Arguments:" in caplog.text
    assert "PPSS_FILE=ppss.yaml" in caplog.text
