from enum import Enum


class DeploymentMethod(Enum):
    DOCKER_COMPOSE = "docker-compose"
    PM2 = "pm2"
    K8S = "k8s"

    def __str__(self):
        return self.value

    @property
    def extension(self) -> str:
        if self == DeploymentMethod.DOCKER_COMPOSE:
            return "yml"
        if self == DeploymentMethod.PM2:
            return "config.js"
        if self == DeploymentMethod.K8S:
            return "yaml"
        raise ValueError(f"Invalid deployment method: {self}")

    @classmethod
    def from_str(cls, s: str):
        if s == "docker-compose":
            return cls.DOCKER_COMPOSE
        if s == "pm2":
            return cls.PM2
        if s == "k8s":
            return cls.K8S
        raise ValueError(f"Invalid deployment method: {s}")

    def run_command(self, foldername, config_name) -> str:
        return f"pdr deployer deploy {config_name}"
