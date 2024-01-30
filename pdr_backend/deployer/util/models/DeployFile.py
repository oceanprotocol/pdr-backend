from dataclasses import dataclass
from pdr_backend.deployer.util.models.DeploymentMethod import DeploymentMethod


@dataclass
class DeployFile:
    method: DeploymentMethod
    content: str
    name: str

    def write(self, directory):
        file_name = self.name.replace("/", "-")
        with open(f"{directory}/{file_name}", "w", encoding="utf-8") as f:
            f.write(self.content)
