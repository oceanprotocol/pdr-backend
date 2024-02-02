from pdr_backend.deployer.util.models.AgentDeployConfig import AgentsDeployConfig
from pdr_backend.deployer.util.models.DeployConfig import DeployConfig


def test_deploy_config():
    agent_config = AgentsDeployConfig(
        agents=[],
        type="predictoor",
        memory="2",
        cpu="1",
    )

    deploy_config = DeployConfig(
        agent_config=agent_config,
        pdr_backend_image_source="oceanprotocol/pdr-backend:latest",
        yaml_path="./ppss.yaml",
    )

    assert isinstance(deploy_config, DeployConfig)
    assert deploy_config.agent_config.type == "predictoor"
    assert deploy_config.pdr_backend_image_source == "oceanprotocol/pdr-backend:latest"
    assert deploy_config.yaml_path == "./ppss.yaml"
