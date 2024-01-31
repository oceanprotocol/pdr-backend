from enum import Enum


class DeploymentMethod(Enum):
    K8S = "k8s"

    def __str__(self):
        return self.value

    @property
    def extension(self) -> str:
        if self == DeploymentMethod.DOCKER_COMPOSE:
            return "yml"
        if self == DeploymentMethod.K8S:
            return "yaml"
        raise ValueError(f"Invalid deployment method: {self}")

    @classmethod
    def from_str(cls, s: str):
        if s == "k8s":
            return cls.K8S
        raise ValueError(f"Invalid deployment method: {s}")

    def deploy_command(self, config_name) -> str:
        return f"pdr deployer deploy {config_name}"
