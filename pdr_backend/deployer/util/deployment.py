# pylint: disable=line-too-long
import shutil
import time
from typing import Optional

from pdr_backend.deployer.util.cloud import CloudProvider, run_command, sanitize_name
from pdr_backend.deployer.util.models.DeploymentInfo import DeploymentInfo


def deploy_agents_with_docker_compose(path, config_name):
    run_command(f"docker-compose -f {path}/{config_name}.yml up")


def destroy_agents_with_docker_compose(path, config_name):
    run_command(f"docker-compose -f {path}/{config_name}.yml down")


def docker_compose_logs(path, config_name):
    run_command(f"docker-compose -f {path}/{config_name}.yml logs -f")


def check_cloud_provider_requirements(provider_name):
    # check if kubectl is installed
    if not shutil.which("kubectl"):
        raise Exception("kubectl is not installed")

    if provider_name == "gcp":
        # check if gcloud is installed
        if not shutil.which("gcloud"):
            raise Exception(
                "gcloud is not installed, install it from https://cloud.google.com/sdk/docs/install"
            )

        if not shutil.which("gke-gcloud-auth-plugin"):
            # pylint: disable=line-too-long
            raise Exception(
                "gke-gcloud-auth-plugin is not installed, run 'gcloud components install gke-gcloud-auth-plugin'"
            )

    if provider_name == "aws":
        # check if aws is installed
        if not shutil.which("aws"):
            raise Exception(
                "aws is not installed, install it from https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html"
            )

    if provider_name == "azure":
        # check if az is installed
        if not shutil.which("az"):
            raise Exception(
                "az is not installed, install it from https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
            )


def check_image_build_requirements():
    # check if docker is installed
    if not shutil.which("docker"):
        raise Exception(
            "docker is not installed, install it from https://docs.docker.com/get-docker/"
        )


def build_image(image_name, image_tag):
    print("Building docker image...")
    run_command(f"docker build -t {image_name}:{image_tag} .")


def push_image(image_name, image_tag, registry_name):
    print("Pushing docker image...")
    run_command(
        f"docker tag {image_name}:{image_tag} {registry_name}/{image_name}:{image_tag}"
    )
    run_command(f"docker push {registry_name}/{image_name}:{image_tag}")


def deploy_agents_to_k8s(config_folder: str, config_name: str):
    config_name_sanitized = sanitize_name(config_name)
    create_namespace(config_name_sanitized)
    run_command(f"kubectl apply -f {config_folder}/ -n {config_name_sanitized}")


def deploy_cluster(provider: CloudProvider, cluster_name):
    cluster_name = sanitize_name(cluster_name)
    if not provider.cluster_exists(cluster_name):
        print("Creating Kubernetes cluster...")
        provider.create_kubernetes_cluster(cluster_name)


def create_namespace(namespace: str):
    run_command(f"kubectl create namespace {namespace}")


def destroy_cluster(provider: CloudProvider, cluster_name, config_name):
    cluster_name_sanitized = sanitize_name(cluster_name)
    config_name_sanitized = sanitize_name(config_name)
    if provider.cluster_exists(cluster_name_sanitized):
        should_destroy_cluster = input(
            "Deleting all the pods. Would you like to destroy the cluster? (y/n): "
        )
        if should_destroy_cluster == "y":
            provider.delete_kubernetes_cluster(cluster_name_sanitized)
            print("Destroying Kubernetes cluster...")
        else:
            print("Not destroying the cluster")
            delete_all_pods(provider, cluster_name_sanitized, config_name_sanitized)
    else:
        raise Exception("Cluster does not exist")


def deploy_registry(provider: CloudProvider, registry_name):
    registry_name = sanitize_name(registry_name)
    if not provider.registry_exists(registry_name):
        print("Creating container registry...")
        provider.create_container_registry(registry_name)
        provider.print_registry_url(registry_name)
        provider.auth_registry(registry_name)


def delete_registry(provider: CloudProvider, registry_name):
    registry_name = sanitize_name(registry_name)
    if provider.registry_exists(registry_name):
        print("Destroying container registry...")
        provider.delete_registry(registry_name)


def delete_all_pods(provider: CloudProvider, cluster_name, config_name):
    cluster_name = sanitize_name(cluster_name)
    config_name = sanitize_name(config_name)
    if provider.cluster_exists(cluster_name):
        print("Deleting all pods...")
        command = f"kubectl delete pods --all -n {config_name}"
        run_command(command)


def cluster_logs(provider: CloudProvider, cluster_name, app_name, config_name):
    cluster_name = sanitize_name(cluster_name)
    config_name = sanitize_name(config_name)
    if provider.cluster_exists(cluster_name):
        print("Getting cluster logs...")
        command = f"kubectl get pods -n {config_name}"
        run_command(command)
        command = f"kubectl logs -l app={app_name} -f -n {config_name}"
        run_command(command)


def deploy_config(config_file: str, cloud_provider: Optional[CloudProvider]):
    deploymentinfo = DeploymentInfo.read("./.deployments", config_file)
    deployment_name = deploymentinfo.config_name

    print(f"Deploying {deployment_name}...")
    deployment_folder = deploymentinfo.foldername

    if deploymentinfo.deployment_method == "k8s":
        if cloud_provider is None:
            raise Exception(
                "Cloud provider is required to deploy a Kubernetes deployment"
            )
        check_cloud_provider_requirements(cloud_provider.json["type"])
        deploy_cluster(cloud_provider, deployment_name)
        cloud_provider.auth_kubernetes_cluster(deployment_name)
        print("Cluster is ready, deploying the agents...")
        deploy_agents_to_k8s(deployment_folder, deploymentinfo.config_name)

        deploymentinfo.deployments[cloud_provider.json["type"]] = cloud_provider.json
        deploymentinfo.deployments[cloud_provider.json["type"]].update(
            {
                "deployment_name": deployment_name,
                "deployment_ts": int(time.time()),
                "deployment_method": deploymentinfo.deployment_method,
            }
        )
        deploymentinfo.write("./.deployments")
    if deploymentinfo.deployment_method == "docker-compose":
        deploy_agents_with_docker_compose(deployment_folder, deploymentinfo.config_name)


def destroy_config(config_file: str, cloud_provider: Optional[CloudProvider]):
    deploymentinfo = DeploymentInfo.read("./.deployments", config_file)
    if deploymentinfo.deployment_method == "k8s":
        if cloud_provider is None:
            raise Exception(
                "Cloud provider is required to destroy a Kubernetes deployment"
            )
        check_cloud_provider_requirements(cloud_provider.json["type"])
        deployment_name = deploymentinfo.config_name
        print(f"Destroying {deployment_name}...")
        destroy_cluster(cloud_provider, deployment_name, deploymentinfo.config_name)
        print("Cluster is destroyed")

    if deploymentinfo.deployment_method == "docker-compose":
        deployment_folder = deploymentinfo.foldername
        destroy_agents_with_docker_compose(
            deployment_folder, deploymentinfo.config_name
        )


def logs_config(config_file: str, cloud_provider: Optional[CloudProvider]):
    deploymentinfo = DeploymentInfo.read("./.deployments", config_file)
    if deploymentinfo.deployment_method == "k8s":
        if cloud_provider is None:
            raise Exception(
                "Cloud provider is required to get logs for a Kubernetes deployment"
            )
        check_cloud_provider_requirements(cloud_provider.json["type"])
        deployment_name = deploymentinfo.config_name
        print(f"Getting logs for {deployment_name}...")
        cluster_logs(
            cloud_provider,
            deployment_name,
            "pdr-predictoor",
            deploymentinfo.config_name,
        )

    if deploymentinfo.deployment_method == "docker-compose":
        docker_compose_logs(deploymentinfo.foldername, deploymentinfo.config_name)
