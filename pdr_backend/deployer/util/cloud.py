# pylint: disable=line-too-long
from abc import ABC, abstractmethod
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
    def print_registry_url(self, registry_name):
        pass

    @abstractmethod
    def auth_registry(self, registry_name):
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

    @classmethod
    def from_json(cls, data):
        if "type" in data:
            if data["type"] == "gcp":
                return GCPProvider.from_json(data)
            if data["type"] == "azure":
                return AzureProvider.from_json(data)
            if data["type"] == "aws":
                return AWSProvider.from_json(data)
        raise ValueError("Invalid JSON data for class instantiation")

    @property
    def json(self):
        raise NotImplementedError()


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

    def print_registry_url(self, registry_name):
        print("Printing container registry URL...")
        command_url = f'gcloud artifacts repositories describe {registry_name} --location={self.zone} --project={self.project_id} --format="value(name)"'
        run_command(command_url)

    def auth_registry(self, registry_name):
        print("Authenticating to container registry...")
        command = f"gcloud auth configure-docker {self.zone}-docker.pkg.dev --quiet"
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
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True
        )
        return result.returncode == 0

    def cluster_exists(self, cluster_name):
        command = f"gcloud container clusters describe {cluster_name} --project={self.project_id} --zone={self.zone}"
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True
        )
        return result.returncode == 0

    @property
    def json(self):
        return {
            "type": "gcp",
            "project_id": self.project_id,
            "zone": self.zone,
        }

    @classmethod
    def from_json(cls, data):
        return cls(
            data["zone"],
            data["project_id"],
        )


class AWSProvider(CloudProvider):
    def __init__(self, region):
        self.region = region

    def create_container_registry(self, registry_name):
        print("Creating container registry in AWS...")
        command = f"aws ecr create-repository --repository-name {registry_name}"
        run_command(command)

    def print_registry_url(self, registry_name):
        print("Printing container registry URL...")
        print(
            f"AWS ECR URL: {self.region}.dkr.ecr.{self.region}.amazonaws.com/{registry_name}"
        )

    def auth_registry(self, registry_name):
        print("Authenticating to container registry...")
        command = f"aws ecr get-login-password --region {self.region} | docker login --username AWS --password-stdin {self.region}.dkr.ecr.{self.region}.amazonaws.com"
        run_command(command)

    def create_kubernetes_cluster(self, cluster_name):
        print("Creating Kubernetes cluster in AWS...")
        command = f"eksctl create cluster --name {cluster_name} --region {self.region}"
        run_command(command)

    def delete_registry(self, registry_name):
        print("Destroying container registry...")
        command = f"aws ecr delete-repository --repository-name {registry_name}"
        run_command(command)

    def delete_kubernetes_cluster(self, cluster_name):
        print("Destroying Kubernetes cluster...")
        command = f"eksctl delete cluster --name {cluster_name} --region {self.region}"
        run_command(command)

    def registry_exists(self, registry_name):
        command = f"aws ecr describe-repositories --repository-names {registry_name}"
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True
        )
        return result.returncode == 0

    def cluster_exists(self, cluster_name):
        command = f"eksctl get cluster --name {cluster_name} --region {self.region}"
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True
        )
        return result.returncode == 0

    @property
    def json(self):
        return {
            "type": "aws",
            "region": self.region,
        }

    @classmethod
    def from_json(cls, data):
        return cls(
            data["region"],
        )


class AzureProvider(CloudProvider):
    def __init__(self, subscription_id, resource_group):
        self.subscription_id = subscription_id
        self.resource_group = resource_group

    def create_container_registry(self, registry_name):
        print("Creating container registry in Azure...")
        command = f"az acr create --name {registry_name} --resource-group {self.resource_group} --sku Basic"
        run_command(command)

    def print_registry_url(self, registry_name):
        print("Printing container registry URL...")
        print(f"Azure Container Registry URL: {registry_name}.azurecr.io")

    def auth_registry(self, registry_name):
        print("Authenticating to container registry...")
        command = f"az acr login --name {registry_name} --resource-group {self.resource_group}"
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
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True
        )
        return result.returncode == 0

    def azure_cluster_exists(self, cluster_name):
        command = (
            f"az aks show --name {cluster_name} --resource-group {self.resource_group}"
        )
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True
        )
        return result.returncode == 0

    @property
    def json(self):
        return {
            "type": "azure",
            "subscription_id": self.subscription_id,
            "resource_group": self.resource_group,
        }

    @classmethod
    def from_json(cls, data):
        return cls(
            data["subscription_id"],
            data["resource_group"],
        )
