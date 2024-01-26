from dataclasses import dataclass
from pdr_backend.deployer.util.models.DeploymentMethod import DeploymentMethod


@dataclass
class DeployFile:
    method: DeploymentMethod
    content: str
    name: str

    def write(self, dir):
        file_name = self.name.replace("/", "-")
        with open(f"{dir}/{file_name}", "w", encoding="utf-8") as f:
            f.write(self.content)
