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
