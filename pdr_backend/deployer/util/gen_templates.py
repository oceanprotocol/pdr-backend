import logging
import sys
import os

import time

import yaml

from pdr_backend.deployer.util.config import parse_config
from pdr_backend.deployer.util.models.AgentDeployConfig import AgentsDeployConfig
from pdr_backend.deployer.util.models.PredictoorAgentConfig import PredictoorAgentConfig
from pdr_backend.deployer.util.models.DeployConfig import DeployConfig
from pdr_backend.deployer.util.models.DeploymentInfo import DeploymentInfo
from pdr_backend.deployer.util.models.DeploymentMethod import DeploymentMethod
from pdr_backend.deployer.util.wallet import generate_new_keys, read_keys_json

logger = logging.getLogger("deployer_templates")


def generate_deployment_templates(
    path, output_path, deployment_method: DeploymentMethod, config_name: str
):
    # check if any files in output_path
    if os.path.exists(output_path) and len(os.listdir(output_path)) > 0:
        logger.error("Output path %s is not empty", output_path)
        sys.exit(1)

    deployment_config: DeployConfig = parse_config(path, config_name)
    config: AgentsDeployConfig = deployment_config.agent_config
    # set the private keys

    deployment_names = []
    if config.type == "predictoor":
        predictoor_keys = read_keys_json(config_name)
        diff_keys = len(config.agents) * 2 - len(predictoor_keys)
        if diff_keys > 0:
            predictoor_keys = generate_new_keys(config_name, diff_keys)

        for idx in range(0, len(config.agents)):
            agent: PredictoorAgentConfig = config.agents[idx]  # type: ignore
            pk1, pk2 = predictoor_keys[idx * 2], predictoor_keys[idx * 2 + 1]
            agent.set_private_key(pk1.private_key)
            agent.set_private_key_2(pk2.private_key)  # type: ignore

        if not os.path.exists(output_path):
            os.makedirs(output_path)
        for template in deployment_config.predictoor_templates(deployment_method):
            template.write(output_path)
            deployment_names.append(template.name)
    else:
        raise ValueError(f"Config type {config.type} is not supported")

    logger.info("Generated %s templates for %s", deployment_method, config_name)
    logger.info("  Output path: %s", output_path)
    logger.info("  Config name: %s", config_name)
    logger.info("  Deployment method: %s", deployment_method)
    logger.info("  Number of agents: %d", len(config.agents))
    deploy_command = deployment_method.deploy_command(config_name)
    logger.info("To deploy: %s", deploy_command)

    with open(path, "r") as file:
        deploymentinfo = DeploymentInfo(
            config=yaml.safe_load(file),
            foldername=output_path,
            config_name=config_name,
            deployment_method=str(deployment_method),
            ts_created=int(time.time()),
            deployment_names=deployment_names,
        )

    # write into ./.deployments
    # check if ./.deployments exists
    if not os.path.exists("./.deployments"):
        os.makedirs("./.deployments")
    deploymentinfo.write("./.deployments")
