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
