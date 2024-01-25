import sys
import os

import argparse
import time

import yaml

from deployer.config import parse_config
from deployer.models.AgentDeployConfig import AgentsDeployConfig
from deployer.models.DeployConfig import DeployConfig
from deployer.models.DeploymentInfo import DeploymentInfo
from deployer.models.DeploymentMethod import DeploymentMethod
from deployer.wallet import generate_new_keys, read_keys_json
from deployer.cloud import (
    AWSProvider,
    AzureProvider,
    CloudProvider,
    GCPProvider,
    deploy_agents_to_k8s,
    deploy_cluster,
)
from deployer.cloud import (
    check_requirements as check_cloud_requirements,
    check_image_build_requirements,
)


def generate_deployment_templates(
    path, output_path, deployment_method: DeploymentMethod, config_name: str
):
    # check if any files in output_path
    if os.path.exists(output_path) and len(os.listdir(output_path)) > 0:
        print(f"Output path {output_path} is not empty")
        sys.exit(1)

    deploy_config: DeployConfig = parse_config(path, config_name)
    config: AgentsDeployConfig = deploy_config.agent_config
    # set the private keys
    predictoor_keys = read_keys_json(config_name)
    diff_keys = len(config.agents) - len(predictoor_keys)
    if diff_keys > 0:
        predictoor_keys = generate_new_keys(config_name, diff_keys)
    for idx in range(len(config.agents)):
        config.agents[idx].set_private_key(predictoor_keys[idx].private_key)

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    deployment_names = []
    if config.type == "predictoor":
        for template in deploy_config.predictoor_templates(deployment_method):
            template.write(output_path)
            deployment_names.append(template.name)
    else:
        raise ValueError(f"Config type {config.type} is not supported")

    print(f"Generated {deployment_method} templates for {config_name}")
    print(f"  Output path: {output_path}")
    print(f"  Config name: {config_name}")
    print(f"  Deployment method: {deployment_method}")
    print(f"  Number of agents: {len(config.agents)}")
    run_cmd = deployment_method.run_command(output_path, config_name)
    print(f"Run command: {run_cmd}")

    deploymentinfo = DeploymentInfo(
        config=yaml.safe_load(open(path, "r")),
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


def deploy_existing_config(config_file: str, cloud_provider: CloudProvider):
    # read config from ./.deployments
    deploymentinfo = DeploymentInfo.read("./.deployments", config_file)
    deployment_name = deploymentinfo.config_name
    should_build_image = False
    image_name = deploymentinfo.config["deployment_configs"][deployment_name][
        "pdr_backend_image_source"
    ]

    if not image_name.startswith("oceanprotocol/"):
        check_image_build_requirements()
        should_build_image = True

    if should_build_image:
        raise Exception("Image build is not supported yet")

    print(f"Deploying {deployment_name}...")
    deploy_cluster(cloud_provider, deployment_name)

    print(f"Cluster is ready, deploying the agents...")
    deployment_folder = deploymentinfo.foldername
    deploy_agents_to_k8s(deployment_folder)


def main():
    parser = argparse.ArgumentParser(
        prog="deployer",
        description="Generate and manage deployments Predictoor",
    )

    # Create a subparser for the commands
    subparsers = parser.add_subparsers(dest="command", help="sub-command help")

    # Adding the 'generate' command
    parser_generate = subparsers.add_parser("generate", help="generate help")
    parser_generate.add_argument("config_path", help="Path to the configuration file")
    parser_generate.add_argument("config_name", help="Name of the configuration")
    parser_generate.add_argument(
        "deployment_method",
        help="Method of deployment",
        choices=["k8s", "pm2", "docker-compose"],
    )
    parser_generate.add_argument(
        "output_dir", help="Output directory for the generated files"
    )

    # Adding the 'deploy' command
    parser_deploy = subparsers.add_parser("deploy", help="deploy help")
    parser_deploy.add_argument("config_name", help="Name of the configuration")
    parser_deploy.add_argument(
        "-p",
        "--provider",
        help="Cloud provider",
        required=True,
        choices=["aws", "azure", "gcp"],
    )
    parser_deploy.add_argument(
        "-r",
        "--region",
        required=True,
        help="Deployment zone/region",
    )
    parser_deploy.add_argument(
        "--project_id",
        help="Google Cloud project id",
        required=False,
    )
    # Parse the arguments
    args = parser.parse_args()

    if args.command == "generate":
        generate_deployment_templates(
            args.config_path,
            args.output_dir,
            DeploymentMethod.from_str(args.deployment_method),
            args.config_name,
        )
    elif args.command == "deploy":
        if args.provider == "gcp":
            if not args.project_id:
                raise Exception("Google Cloud project id is required")
            provider = GCPProvider(args.region, args.project_id)
        elif args.provider == "aws":
            provider = AWSProvider(args.region)
        elif args.provider == "azure":
            provider = AzureProvider(args.region)

        check_cloud_requirements(provider)

        deploy_existing_config(args.config_name + "-k8s", provider)
