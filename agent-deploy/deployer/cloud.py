from abc import ABC, abstractmethod
import shutil
import subprocess


def run_command(command):
    print(f"Running command: {command}")
    result = subprocess.run(command, shell=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Error executing {' '.join(command)}: {result.stderr}")
    return result.stdout


class CloudProvider(ABC):
    @abstractmethod
    def create_container_registry(self, registry_name):
        pass

    @abstractmethod
    def create_kubernetes_cluster(self, cluster_name):
        pass

    @abstractmethod
    def delete_registry(self, registry_name):
        pass

    @abstractmethod
    def delete_kubernetes_cluster(self, cluster_name):
        pass

    @abstractmethod
    def registry_exists(self, registry_name) -> bool:
        pass

    @abstractmethod
    def cluster_exists(self, cluster_name) -> bool:
        pass


def sanitize_name(name):
    return name.replace("_", "-")


class GCPProvider(CloudProvider):
    def __init__(self, zone, project_id):
        self.project_id = project_id
        self.zone = zone

    def create_container_registry(self, registry_name):
        print("Creating container registry in GCP...")
        command = f"gcloud artifacts repositories create {registry_name} --repository-format=docker --location={self.zone} --project={self.project_id}"
        run_command(command)

    def create_kubernetes_cluster(self, cluster_name):
        print("Creating Kubernetes cluster in GCP...")
        command = f"gcloud container clusters create-auto {cluster_name} --project={self.project_id} --zone={self.zone}"
        run_command(command)

    def delete_registry(self, registry_name):
        print("Destroying container registry...")
        command = f"gcloud artifacts repositories delete {registry_name} --location={self.zone} --project={self.project_id} --quiet"
        run_command(command)

    def delete_kubernetes_cluster(self, cluster_name):
        print("Destroying Kubernetes cluster...")
        command = f"gcloud container clusters delete {cluster_name} --project={self.project_id} --zone={self.zone} --quiet"
        run_command(command)

    def registry_exists(self, registry_name):
        command = f"gcloud artifacts repositories describe {registry_name} --location={self.zone} --project={self.project_id}"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0

    def cluster_exists(self, cluster_name):
        command = f"gcloud container clusters describe {cluster_name} --project={self.project_id} --zone={self.zone}"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0


class AWSProvider(CloudProvider):
    def __init__(self, region):
        self.region = region

    def create_container_registry(self):
        print("Creating container registry in AWS...")

    def create_kubernetes_cluster(self):
        print("Creating Kubernetes cluster in AWS...")


class AzureProvider(CloudProvider):
    def __init__(self, subscription_id, resource_group, region):
        self.subscription_id = subscription_id
        self.resource_group = resource_group

    def create_container_registry(self, registry_name):
        print("Creating container registry in Azure...")
        command = f"az acr create --name {registry_name} --resource-group {self.resource_group} --sku Basic"
        run_command(command)

    def create_kubernetes_cluster(self, cluster_name):
        print("Creating Kubernetes cluster in Azure...")
        command = f"az aks create --resource-group {self.resource_group} --name {cluster_name} --enable-managed-identity --generate-ssh-keys"
        run_command(command)

    def delete_registry_azure(self, registry_name):
        print("Destroying container registry...")
        command = f"az acr delete --name {registry_name} --resource-group {self.resource_group} --yes"
        run_command(command)

    def delete_kubernetes_cluster_azure(self, cluster_name):
        print("Destroying Kubernetes cluster...")
        command = f"az aks delete --name {cluster_name} --resource-group {self.resource_group} --yes"
        run_command(command)

    def azure_registry_exists(self, registry_name):
        command = (
            f"az acr show --name {registry_name} --resource-group {self.resource_group}"
        )
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0

    def azure_cluster_exists(self, cluster_name):
        command = (
            f"az aks show --name {cluster_name} --resource-group {self.resource_group}"
        )
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0


def check_requirements(provider_name):
    # check if kubectl is installed
    if not shutil.which("kubectl"):
        raise Exception("kubectl is not installed")

    if provider_name == "gcp":
        # check if gcloud is installed
        if not shutil.which("gcloud"):
            raise Exception("gcloud is not installed")

        if not shutil.which("gke-gcloud-auth-plugin"):
            raise Exception(
                "gke-gcloud-auth-plugin is not installed, run 'gcloud components install gke-gcloud-auth-plugin'"
            )

    if provider_name == "aws":
        # check if aws is installed
        if not shutil.which("aws"):
            raise Exception("aws is not installed")

    if provider_name == "azure":
        # check if az is installed
        if not shutil.which("az"):
            raise Exception("az is not installed")


def check_image_build_requirements():
    # check if docker is installed
    if not shutil.which("docker"):
        raise Exception("docker is not installed")

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

def delete_all_pods(provider: CloudProvider, cluster_name):
    cluster_name = sanitize_name(cluster_name)
    if provider.cluster_exists(cluster_name):
        print("Deleting all pods...")
        command = f"kubectl delete pods --all"
        run_command(command)

def cluster_logs(provider: CloudProvider, cluster_name, app_name):
    cluster_name = sanitize_name(cluster_name)
    if provider.cluster_exists(cluster_name):
        print("Getting cluster logs...")
        command = f"kubectl logs -l app={app_name}"
        run_command(command)