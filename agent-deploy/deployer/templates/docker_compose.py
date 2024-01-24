from typing import List
from enforce_typing import enforce_types


@enforce_types
def get_docker_compose_template(
    name: str,
    app: str,
    docker_image: str,
    cpu: str,
    memory: str,
    run_command: List[str],
    private_key: str,
) -> str:
    run_command_str = " ".join(run_command)
    template = f""" {name}:
    container_name: {name}
    image: {docker_image}
    command: {run_command_str}
    environment:
      PRIVATE_KEY: "{private_key}"
    deploy:
      resources:
        limits:
          cpus: '{cpu}'
          memory: {memory}
    labels:
      - "app={app}"
    restart: always
    """
    return template
