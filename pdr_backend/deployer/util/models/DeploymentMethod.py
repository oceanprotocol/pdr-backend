#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enum import Enum


class DeploymentMethod(Enum):
    K8S = "k8s"

    def __str__(self):
        return self.value

    @property
    def extension(self) -> str:
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
