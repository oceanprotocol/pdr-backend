# pylint: disable=unused-argument
from unittest.mock import patch, mock_open, MagicMock
from pdr_backend.deployer.util.gen_templates import generate_deployment_templates
from pdr_backend.deployer.util.models.DeploymentMethod import DeploymentMethod


@patch("pdr_backend.deployer.util.gen_templates.generate_new_keys")
@patch("pdr_backend.deployer.util.gen_templates.read_keys_json")
@patch("pdr_backend.deployer.util.gen_templates.parse_config")
@patch("builtins.open", new_callable=mock_open)
@patch("os.makedirs")
@patch("os.path.exists")
def test_generate_deployment_templates_empty_output_path(
    mock_os_path_exists,
    mock_os_makedirs,
    mock_open_file,
    mock_parse_config,
    mock_read_keys_json,
    mock_generate_new_keys,
):
    mock_os_path_exists.return_value = False
    deploy_config_mock = MagicMock()
    deploy_config_mock.agent_config.agents = [MagicMock(), MagicMock()]
    deploy_config_mock.agent_config.type = "predictoor"
    mock_parse_config.return_value = deploy_config_mock
    mock_read_keys_json.return_value = []
    mock_generate_new_keys.return_value = [MagicMock()] * 4

    generate_deployment_templates(
        "path", "output_path", DeploymentMethod.K8S, "config_name"
    )

    mock_open_file.assert_called()
    mock_parse_config.assert_called_once_with("path", "config_name")
    mock_read_keys_json.assert_called_once_with("config_name")
    mock_generate_new_keys.assert_called_once_with("config_name", 4)


@patch("pdr_backend.deployer.util.gen_templates.generate_new_keys")
@patch("pdr_backend.deployer.util.gen_templates.read_keys_json")
@patch("pdr_backend.deployer.util.gen_templates.parse_config")
@patch("builtins.open", new_callable=mock_open)
@patch("os.makedirs")
@patch("os.path.exists")
def test_generate_deployment_templates_with_existing_keys(
    mock_os_path_exists,
    mock_os_makedirs,
    mock_open_file,
    mock_parse_config,
    mock_read_keys_json,
    mock_generate_new_keys,
):
    mock_os_path_exists.return_value = False
    deploy_config_mock = MagicMock()
    deploy_config_mock.agent_config.agents = [MagicMock(), MagicMock()]
    deploy_config_mock.agent_config.type = "predictoor"
    mock_parse_config.return_value = deploy_config_mock
    mock_read_keys_json.return_value = [
        MagicMock(),
        MagicMock(),
        MagicMock(),
        MagicMock(),
    ]
    mock_generate_new_keys.return_value = []

    generate_deployment_templates(
        "path", "output_path", DeploymentMethod.K8S, "config_name"
    )

    mock_open_file.assert_called()
    mock_parse_config.assert_called_once_with("path", "config_name")
    mock_read_keys_json.assert_called_once_with("config_name")
    mock_generate_new_keys.assert_not_called()


@patch("pdr_backend.deployer.util.gen_templates.generate_new_keys")
@patch("pdr_backend.deployer.util.gen_templates.read_keys_json")
@patch("pdr_backend.deployer.util.gen_templates.parse_config")
@patch("builtins.open", new_callable=mock_open)
@patch("os.makedirs")
@patch("os.path.exists")
def test_generate_deployment_templates_needs_new_keys(
    mock_os_path_exists,
    mock_os_makedirs,
    mock_open_file,
    mock_parse_config,
    mock_read_keys_json,
    mock_generate_new_keys,
):
    mock_os_path_exists.return_value = False
    deploy_config_mock = MagicMock()
    deploy_config_mock.agent_config.agents = [MagicMock(), MagicMock()]
    deploy_config_mock.agent_config.type = "predictoor"
    mock_parse_config.return_value = deploy_config_mock
    mock_read_keys_json.return_value = [MagicMock(), MagicMock()]
    mock_generate_new_keys.return_value = [MagicMock()] * 4

    generate_deployment_templates(
        "path", "output_path", DeploymentMethod.K8S, "config_name"
    )

    mock_open_file.assert_called()
    mock_parse_config.assert_called_once_with("path", "config_name")
    mock_read_keys_json.assert_called_once_with("config_name")
    mock_generate_new_keys.assert_called_once_with("config_name", 2)
