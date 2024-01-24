import yaml
from deployer.models.AgentDeployConfig import AgentsDeployConfig

from deployer.models.DeployConfig import DeployConfig
from deployer.models.PredictoorAgentConfig import PredictoorAgentConfig

def parse_config(file_path: str) -> DeployConfig:
    with open(file_path, "r") as file:
        config_data = yaml.safe_load(file)

    predictoor_config_data = config_data["predictoor_config"]
    if not "approach" in predictoor_config_data:
        predictoor_config_data["approach"] = None
    predictoor_agents = [
        PredictoorAgentConfig(**agent) for agent in predictoor_config_data["agents"]
    ]
    predictoor_config = AgentsDeployConfig(
        cpu=predictoor_config_data.get("cpu"),
        memory=predictoor_config_data.get("memory"),
        approach=predictoor_config_data.get("approach"),
        agents=predictoor_agents,
        pdr_backend_image_source=predictoor_config_data.get("pdr_backend_image_source"),
        source=predictoor_config_data.get("source"),
        network=predictoor_config_data.get("network"),
        s_until_epoch_end=predictoor_config_data.get("s_until_epoch_end"),
    )

    deploy_config = DeployConfig(
        predictoor_config=predictoor_config,
        pdr_backend_image_source=config_data.get(
            "pdr_backend_image_source", "oceanprotocol/pdr-backend:latest"
        ),
        yaml_path=config_data.get("yaml_path", "./ppss.yaml"),
    )
    deploy_config.update_defaults()

    return deploy_config
