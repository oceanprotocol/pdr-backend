# pylint: disable=line-too-long
import shutil
import time

from pdr_backend.deployer.util.cloud import CloudProvider, run_command, sanitize_name
from pdr_backend.deployer.util.models.DeploymentInfo import DeploymentInfo


def deploy_agents_with_pm2(path):
    run_command(f"pm2 start {path}/*.js")


def destroy_agents_with_pm2(path):
    run_command(f"pm2 delete {path}/*.js")


def pm2_logs():
    run_command("pm2 logs")


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


def deploy_agents_to_k8s(config_folder: str):
    print("Deploying agents...")
    run_command(f"kubectl apply -f {config_folder}/")


def deploy_cluster(provider: CloudProvider, cluster_name):
    cluster_name = sanitize_name(cluster_name)
    if not provider.cluster_exists(cluster_name):
        print("Creating Kubernetes cluster...")
        provider.create_kubernetes_cluster(cluster_name)


def destroy_cluster(provider: CloudProvider, cluster_name):
    cluster_name = sanitize_name(cluster_name)
    if provider.cluster_exists(cluster_name):
        should_destroy_cluster = input(
            "Deleting all the pods. Would you like to destroy the cluster? (y/n): "
        )
        if should_destroy_cluster == "y":
            provider.delete_kubernetes_cluster(cluster_name)
            print("Destroying Kubernetes cluster...")
        else:
            print("Not destroying the cluster")
            delete_all_pods(provider, cluster_name)


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


def delete_all_pods(provider: CloudProvider, cluster_name):
    cluster_name = sanitize_name(cluster_name)
    if provider.cluster_exists(cluster_name):
        print("Deleting all pods...")
        command = "kubectl delete pods --all"
        run_command(command)


def cluster_logs(provider: CloudProvider, cluster_name, app_name):
    cluster_name = sanitize_name(cluster_name)
    if provider.cluster_exists(cluster_name):
        print("Getting cluster logs...")
        command = f"kubectl logs -l app={app_name}"
        run_command(command)


def deploy_config(config_file: str, cloud_provider: CloudProvider):
    deploymentinfo = DeploymentInfo.read("./.deployments", config_file)
    deployment_name = deploymentinfo.config_name

    print(f"Deploying {deployment_name}...")
    deployment_folder = deploymentinfo.foldername

    if deploymentinfo.deployment_method == "k8s":
        check_cloud_provider_requirements(cloud_provider)
        deploy_cluster(cloud_provider, deployment_name)

        print("Cluster is ready, deploying the agents...")
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
    if deploymentinfo.deployment_method == "pm2":
        deploy_agents_with_pm2(deployment_folder)
    if deploymentinfo.deployment_method == "docker-compose":
        deploy_agents_with_docker_compose(deployment_folder, deploymentinfo.config_name)


def destroy_config(config_file: str, cloud_provider: CloudProvider):
    deploymentinfo = DeploymentInfo.read("./.deployments", config_file)
    if deploymentinfo.deployment_method == "k8s":
        check_cloud_provider_requirements(cloud_provider)
        deployment_name = deploymentinfo.config_name
        print(f"Destroying {deployment_name}...")
        destroy_cluster(cloud_provider, deployment_name)
        print("Cluster is destroyed")

    if deploymentinfo.deployment_method == "pm2":
        deployment_folder = deploymentinfo.foldername
        destroy_agents_with_pm2(deployment_folder)

    if deploymentinfo.deployment_method == "docker-compose":
        deployment_folder = deploymentinfo.foldername
        destroy_agents_with_docker_compose(deployment_folder, deploymentinfo.config_name)


def logs_config(config_file: str, cloud_provider: CloudProvider):
    deploymentinfo = DeploymentInfo.read("./.deployments", config_file)
    if deploymentinfo.deployment_method == "k8s":
        check_cloud_provider_requirements(cloud_provider)
        deployment_name = deploymentinfo.config_name
        print(f"Getting logs for {deployment_name}...")
        cluster_logs(cloud_provider, deployment_name, "pdr-predictoor")

    if deploymentinfo.deployment_method == "pm2":
        pm2_logs()

    if deploymentinfo.deployment_method == "docker-compose":
        docker_compose_logs(deploymentinfo.foldername, deploymentinfo.config_name)
