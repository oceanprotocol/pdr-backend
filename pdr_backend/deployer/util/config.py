import yaml
from pdr_backend.deployer.util.models.AgentDeployConfig import AgentsDeployConfig

from pdr_backend.deployer.util.models.DeployConfig import DeployConfig
from pdr_backend.deployer.util.models.PredictoorAgentConfig import PredictoorAgentConfig


def parse_config(file_path: str, config_name: str) -> DeployConfig:
    with open(file_path, "r") as file:
        config_file_data = yaml.safe_load(file)

    config_data = config_file_data["deployment_configs"][config_name]
    agents = []
    if not "approach" in config_data:
        config_data["approach"] = None

    if config_data.get("type") == "predictoor":
        agents = [PredictoorAgentConfig(private_key="", **agent) for agent in config_data["agents"]]
    else:
        raise ValueError(f"Config type {config_data.get('type')} is not supported")

    agents_deploy_config = AgentsDeployConfig(
        cpu=config_data.get("cpu"),
        memory=config_data.get("memory"),
        approach=config_data.get("approach"),
        agents=agents,
        pdr_backend_image_source=config_data.get("pdr_backend_image_source"),
        source=config_data.get("source"),
        network=config_data.get("network"),
        s_until_epoch_end=config_data.get("s_until_epoch_end"),
        type=config_data.get("type"),
    )

    deploy_config = DeployConfig(
        agent_config=agents_deploy_config,
        pdr_backend_image_source=config_file_data.get(
            "pdr_backend_image_source", "oceanprotocol/pdr-backend:latest"
        ),
        yaml_path=config_file_data.get("yaml_path", "./ppss.yaml"),
    )
    deploy_config.update_defaults()

    return deploy_config
