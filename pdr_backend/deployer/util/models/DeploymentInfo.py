from dataclasses import dataclass
import json
from typing import List


@dataclass
class DeploymentInfo:
    config: dict
    foldername: str
    config_name: str
    deployment_method: str
    ts_created: int
    deployment_names: List[str]

    @property
    def name(self):
        return f"{self.config_name}-{self.deployment_method}"

    def write(self, path):
        with open(f"{path}/{self.name}.json", "w") as f:
            f.write(json.dumps(self.__dict__))

    @classmethod
    def read(cls, path, config_name):
        with open(f"{path}/{config_name}.json", "r") as f:
            config = json.loads(f.read())
        return cls(**config)

    @classmethod
    def from_json(cls, path):
        with open(path, "r") as f:
            config = json.loads(f.read())
        return cls(**config)
