import sys
import os

import argparse
import time

import yaml

from pdr_backend.deployer.util.config import parse_config
from pdr_backend.deployer.util.models.AgentDeployConfig import AgentsDeployConfig
from pdr_backend.deployer.util.models.DeployConfig import DeployConfig
from pdr_backend.deployer.util.models.DeploymentInfo import DeploymentInfo
from pdr_backend.deployer.util.models.DeploymentMethod import DeploymentMethod
from pdr_backend.deployer.util.wallet import generate_new_keys, read_keys_json
from pdr_backend.deployer.util.cloud import (
    AWSProvider,
    AzureProvider,
    CloudProvider,
    GCPProvider,
    build_image,
    cluster_logs,
    delete_registry,
    deploy_agents_to_k8s,
    deploy_cluster,
    deploy_registry,
    destroy_cluster,
    push_image,
)
from pdr_backend.deployer.util.cloud import (
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
    print(f"Run subcommand: {run_cmd}")

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


def deploy_config(config_file: str, cloud_provider: CloudProvider):
    deploymentinfo = DeploymentInfo.read("./.deployments", config_file)
    deployment_name = deploymentinfo.config_name

    print(f"Deploying {deployment_name}...")
    deploy_cluster(cloud_provider, deployment_name)

    print(f"Cluster is ready, deploying the agents...")
    deployment_folder = deploymentinfo.foldername
    deploy_agents_to_k8s(deployment_folder)

    deploymentinfo.deployments[cloud_provider.json["type"]] = cloud_provider.json
    deploymentinfo.deployments[cloud_provider.json["type"]].update(
        {
            "deployment_name": deployment_name,
            "deployment_ts": int(time.time()),
            "deployment_method": deploymentinfo.deployment_method,
        }
    )
    deploymentinfo.write("./.deployments")


def destroy_existing_config(config_file: str, cloud_provider: CloudProvider):
    deploymentinfo = DeploymentInfo.read("./.deployments", config_file)
    deployment_name = deploymentinfo.config_name
    print(f"Destroying {deployment_name}...")
    destroy_cluster(cloud_provider, deployment_name)
    print(f"Cluster is destroyed")


def get_provider(args):
    if hasattr(args, "config_name"):
        config = DeploymentInfo.read("./.deployments", args.config_name)
        if config.deployments.get(args.provider):
            return CloudProvider.from_json(config.deployments[args.provider])

    if args.provider == "gcp":
        if not args.project_id:
            raise Exception("Google Cloud project id is required")
        provider = GCPProvider(args.region, args.project_id)
    elif args.provider == "aws":
        provider = AWSProvider(args.region)
    elif args.provider == "azure":
        provider = AzureProvider(args.region)
    else:
        raise Exception(f"Unknown provider {args.provider}")
    return provider


def main(args):
    if args.subcommand == "generate":
        generate_deployment_templates(
            args.config_path,
            args.output_dir,
            DeploymentMethod.from_str(args.deployment_method),
            args.config_name,
        )
    elif args.subcommand == "deploy":
        provider = get_provider(args)
        check_cloud_requirements(provider)
        deploy_config(args.config_name, provider)
    elif args.subcommand == "destroy":
        provider = get_provider(args)
        check_cloud_requirements(provider)
        destroy_existing_config(args.config_name, provider)
    elif args.subcommand == "logs":
        provider = get_provider(args)
        check_cloud_requirements(provider)
        cluster_logs(provider, args.config_name, "pdr-predictoor")
    elif args.subcommand == "build":
        check_image_build_requirements()
        build_image(args.image_name, args.image_tag)
    elif args.subcommand == "push":
        check_image_build_requirements()
        push_image(args.image_name, args.image_tag, args.registry_name, args.image_name)
    elif args.subcommand == "registry":
        provider = get_provider(args)
        check_cloud_requirements(provider)
        if args.action == "deploy":
            deploy_registry(provider, args.registry_name)
        elif args.action == "destroy":
            delete_registry(provider, args.registry_name)
        else:
            raise Exception(f"Unknown subcommand {args.subcommand}")


if __name__ == "__main__":
    main()
