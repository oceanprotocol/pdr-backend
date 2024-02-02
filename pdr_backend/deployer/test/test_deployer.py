import pytest
from unittest.mock import patch, MagicMock
from pdr_backend.deployer.deployer import main, get_provider
from pdr_backend.deployer.util.models.DeploymentMethod import DeploymentMethod


class MockArgs:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_get_provider_gcp_required_project_id():
    args = MockArgs(provider="gcp", region="us-central1", project_id=None)
    with pytest.raises(Exception) as excinfo:
        get_provider(args)
    assert "Google Cloud project id is required" in str(excinfo.value)


@patch("pdr_backend.deployer.deployer.generate_deployment_templates")
def test_main_generate(mock_generate):
    args = MockArgs(
        subcommand="generate",
        config_path="./configs",
        output_dir="./output",
        deployment_method="k8s",
        config_name="config1",
    )
    main(args)
    mock_generate.assert_called_once_with(
        "./configs", "./output", DeploymentMethod.K8S, "config1"
    )


def test_get_provider_gcp_success():
    args = MockArgs(provider="gcp", region="us-central1", project_id="test-project")
    provider = get_provider(args)
    assert provider.json["type"] == "gcp"
    assert provider.project_id == "test-project"


def test_main_unknown_subcommand():
    args = MockArgs(
        provider="gcp",
        subcommand="destroy",
        deployment_id="deployment123",
        project_id=None,
    )
    with pytest.raises(Exception) as err:
        main(args)
    assert "Google Cloud project id is required" in str(err.value)
