from dataclasses import dataclass
import json
from typing import List


@dataclass
class DeploymentInfo:
    config: dict
    foldername: str
    config_name: str
    deployment_method: str
    is_deployed: bool
    ts_created: int
    deployment_names: List[str]

    @property
    def name(self):
        return f"{self.config_name}-{self.deployment_method}-{self.ts_created}"

    def write(self, path):
        with open(f"{path}/{self.name}.json", "w") as f:
            f.write(json.dumps(self.__dict__))

    @classmethod
    def from_json(cls, path):
        with open(path, "r") as f:
            config = json.loads(f.read())
        return cls(**config)
