from unittest.mock import Mock, patch

import yaml

from pdr_backend.ppss.ppss import fast_test_yaml_str
from pdr_backend.util.cli_module import do_publisher


@patch("pdr_backend.util.cli_module.publish_assets")
@patch("pdr_backend.util.cli_module.print_args")
@patch("builtins.open")
# pylint: disable = redefined-builtin, unused-argument
def test_main(
    mock_agent_init,
    mock_agent_run,
    open,
    tmpdir,
):
    with patch("pdr_backend.util.cli_module.PublisherArgParser") as m:
        m.return_value = Mock()
        m.return_value.parse_args = Mock()

        test_yaml = fast_test_yaml_str(tmpdir)
        loaded_yaml = yaml.safe_load(test_yaml)

        m.parse_args = Mock()

        with patch("pdr_backend.ppss.ppss.yaml.safe_load") as t:
            t.return_value = loaded_yaml

            class MockArgs:
                def __init__(self) -> None:
                    self.NETWORK = "development"
                    self.YAML_FILE = "test.yml"

                def __repr__(self) -> str:
                    return f"{self.NETWORK}, {self.YAML_FILE}"

            m.return_value.parse_args.return_value = MockArgs()

            do_publisher()
            mock_agent_init.assert_called_once()
            mock_agent_run.assert_called_once()
