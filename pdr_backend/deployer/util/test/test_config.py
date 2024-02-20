# pylint: disable=redefined-outer-name
import pytest
from pdr_backend.deployer.util.models.DeployConfig import DeployConfig
from pdr_backend.deployer.util.models.AgentDeployConfig import AgentsDeployConfig
from pdr_backend.deployer.util.models.PredictoorAgentConfig import PredictoorAgentConfig
from pdr_backend.deployer.util.models.DeploymentMethod import DeploymentMethod


@pytest.fixture
def sample_agents_deploy_config():
    agents = [
        PredictoorAgentConfig(
            private_key="0x1",
            pair="BTC/USDT",
            timeframe="5m",
            stake_amt=100,
            approach=1,
            source="binance",
            cpu="1",
            memory="2",
            network="mainnet",
            s_until_epoch_end=60,
        )
    ]
    return AgentsDeployConfig(
        agents=agents,
        pdr_backend_image_source="oceanprotocol/pdr-backend:latest",
        type="predictoor",
        memory="2",
        cpu="1",
    )


@pytest.fixture
def sample_deploy_config(sample_agents_deploy_config):
    return DeployConfig(
        agent_config=sample_agents_deploy_config,
        yaml_path="./ppss.yaml",
    )


def test_update_defaults(sample_deploy_config):
    sample_deploy_config.update_defaults()
    for agent in sample_deploy_config.agent_config.agents:
        assert agent.cpu == sample_deploy_config.agent_config.cpu
        assert agent.memory == sample_deploy_config.agent_config.memory


def test_predictoor_templates(sample_deploy_config):
    templates = sample_deploy_config.predictoor_templates(DeploymentMethod.K8S)
    assert len(templates) == len(sample_deploy_config.agent_config.agents)
    for template in templates:
        assert template.method == DeploymentMethod.K8S
        assert ".yaml" in template.name


def test_predictoor_template(sample_deploy_config):
    template, name = sample_deploy_config.predictoor_template(0, DeploymentMethod.K8S)
    assert "pdr-predictoor" in name
    assert sample_deploy_config.agent_config.agents[0].pair in template
    assert sample_deploy_config.agent_config.pdr_backend_image_source in template
