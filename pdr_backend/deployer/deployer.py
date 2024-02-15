from pdr_backend.deployer.util.gen_templates import generate_deployment_templates
from pdr_backend.deployer.util.deployment import (
    build_image,
    check_image_build_requirements,
    check_cloud_provider_requirements,
    delete_registry,
    deploy_config,
    deploy_registry,
    destroy_config,
    logs_config,
    push_image,
)
from pdr_backend.deployer.util.models.DeploymentInfo import DeploymentInfo
from pdr_backend.deployer.util.models.DeploymentMethod import DeploymentMethod
from pdr_backend.deployer.util.cloud import (
    AWSProvider,
    AzureProvider,
    CloudProvider,
    GCPProvider,
)


def get_provider(args):
    if hasattr(args, "config_name"):
        config = DeploymentInfo.read("./.deployments", args.config_name)
        provider_name = config.deployments.get(args.provider)
        if provider_name:
            return CloudProvider.from_json(config.deployments[args.provider])

        # check if there's only one deployment config, in that case, use that
        if len(config.deployments) == 1:
            return CloudProvider.from_json(list(config.deployments.values())[0])

    if args.provider is None:
        return None

    if args.provider == "gcp":
        if not args.project_id:
            raise Exception("Google Cloud project id is required")
        provider = GCPProvider(args.region, args.project_id)
    elif args.provider == "aws":
        provider = AWSProvider(args.region)
    elif args.provider == "azure":
        provider = AzureProvider(args.region, args.resource_group)
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
        deploy_config(args.config_name, provider)
    elif args.subcommand == "destroy":
        provider = get_provider(args)
        destroy_config(args.config_name, provider)
    elif args.subcommand == "logs":
        provider = get_provider(args)
        logs_config(args.config_name, provider)
    elif args.subcommand == "build":
        check_image_build_requirements()
        build_image(args.image_name, args.image_tag)
    elif args.subcommand == "push":
        check_image_build_requirements()
        push_image(args.image_name, args.image_tag, args.registry_name, args.image_name)
    elif args.subcommand == "registry":
        provider = get_provider(args)
        check_cloud_provider_requirements(provider)
        if args.action == "deploy":
            deploy_registry(provider, args.registry_name)
        elif args.action == "destroy":
            delete_registry(provider, args.registry_name)
        elif args.action == "url":
            provider.print_registry_url(args.registry_name)
        elif args.action == "auth":
            provider.auth_registry(args.registry_name)
        else:
            raise Exception(f"Unknown subcommand {args.subcommand}")
