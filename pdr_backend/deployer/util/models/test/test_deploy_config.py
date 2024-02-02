# pylint: disable=redefined-outer-name, unused-argument
from unittest.mock import MagicMock, patch
import pytest
from pdr_backend.deployer.util.models.DeployConfig import DeployConfig
from pdr_backend.deployer.util.models.AgentDeployConfig import AgentsDeployConfig
from pdr_backend.deployer.util.models.DeploymentMethod import DeploymentMethod


@pytest.fixture
def mock_agents_deploy_config():
    mock = MagicMock(spec=AgentsDeployConfig)
    mock.agents = [MagicMock(), MagicMock()]
    return mock


@pytest.fixture
def deploy_config(mock_agents_deploy_config):
    return DeployConfig(agent_config=mock_agents_deploy_config)


def test_update_defaults(deploy_config, mock_agents_deploy_config):
    deploy_config.update_defaults()
    for agent in mock_agents_deploy_config.agents:
        agent.update_with_defaults.assert_called_once_with(mock_agents_deploy_config)


@patch("pdr_backend.deployer.util.models.DeployConfig.get_k8s_predictoor_template")
def test_predictoor_template_k8s(mock_get_k8s_template, deploy_config):
    mock_get_k8s_template.return_value = "template_content"
    index = 0
    method = DeploymentMethod.K8S
    template, name = deploy_config.predictoor_template(index, method)
    assert template == "template_content"
    assert "pdr-predictoor" in name
    mock_get_k8s_template.assert_called_once()


def test_predictoor_templates(deploy_config):
    with patch.object(deploy_config, "predictoor_template") as mock_predictoor_template:
        mock_predictoor_template.return_value = ("template_content", "template_name")
        templates = deploy_config.predictoor_templates(DeploymentMethod.K8S)
        assert len(templates) == len(deploy_config.agent_config.agents)
        for template in templates:
            assert template.content == "template_content"
            assert "template_name" in template.name
        assert mock_predictoor_template.call_count == len(
            deploy_config.agent_config.agents
        )


def test_unsupported_deployment_method(deploy_config):
    with pytest.raises(Exception) as excinfo:
        deploy_config.predictoor_template(0, "unsupported_method")
    assert "Deployment method" in str(excinfo.value)
