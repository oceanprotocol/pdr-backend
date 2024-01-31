from dataclasses import dataclass
from typing import List, Tuple
from pdr_backend.deployer.util.models.AgentDeployConfig import AgentsDeployConfig
from pdr_backend.deployer.util.models.DeployFile import DeployFile
from pdr_backend.deployer.util.models.DeploymentMethod import DeploymentMethod
from pdr_backend.deployer.util.templates.docker_compose import (
    get_docker_compose_template,
)
from pdr_backend.deployer.util.templates.k8s import get_k8s_predictoor_template


@dataclass
class DeployConfig:
    agent_config: AgentsDeployConfig
    pdr_backend_image_source: str = "oceanprotocol/pdr-backend:latest"
    yaml_path: str = "./ppss.yaml"

    def update_defaults(self):
        for agent in self.agent_config.agents:
            agent.update_with_defaults(self.agent_config)

    def predictoor_templates(self, method: DeploymentMethod) -> List[DeployFile]:
        templates: List[DeployFile] = []
        for idx in range(len(self.agent_config.agents)):
            template, name = self.predictoor_template(idx, method)
            deploy_file = DeployFile(
                method=method, content=template, name=f"{name}.{method.extension}"
            )
            templates.append(deploy_file)
        return templates

    def predictoor_template(self, index, method: DeploymentMethod) -> Tuple[str, str]:
        predictoor = self.agent_config.agents[index]
        full_pair_name = (
            f"{predictoor.source} {predictoor.pair} c {predictoor.timeframe}"
        )
        # pylint: disable=line-too-long
        full_name = f"pdr-predictoor{index + 1}-{predictoor.approach}-{predictoor.pair}-{predictoor.timeframe}-{predictoor.source}"
        full_name = full_name.replace("/", "-")
        run_command = predictoor.get_run_command(
            predictoor.stake_amt,
            predictoor.approach,
            full_pair_name,
            predictoor.network,
            predictoor.s_until_epoch_end,
            self.yaml_path,
            with_apostrophe=method == DeploymentMethod.DOCKER_COMPOSE,
        )
        if method == DeploymentMethod.K8S:
            return (
                get_k8s_predictoor_template(
                    name=full_name,
                    app="pdr-predictoor",
                    docker_image=self.agent_config.pdr_backend_image_source,
                    cpu=predictoor.cpu,
                    memory=predictoor.memory,
                    private_key=predictoor.private_key,
                    run_command=run_command,
                ),
                full_name,
            )

        if method == DeploymentMethod.DOCKER_COMPOSE:
            return (
                get_docker_compose_template(
                    name=full_name,
                    app="pdr-predictoor",
                    docker_image=predictoor.pdr_backend_image_source,
                    private_key=predictoor.private_key,
                    run_command=run_command,
                    cpu=predictoor.cpu,
                    memory=predictoor.memory,
                ),
                full_name,
            )

        raise Exception(f"Deployment method {type} not supported")

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
