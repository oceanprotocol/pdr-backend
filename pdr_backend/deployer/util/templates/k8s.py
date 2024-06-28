#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types


@enforce_types
def get_k8s_predictoor_template(
    name,
    app,
    docker_image,
    cpu,
    memory,
    private_key,
    private_key_2,
    run_command,
):
    run_command_args = ""
    app = app.lower()
    name = name.lower()
    for arg in run_command[1:]:
        run_command_args += f"          - {arg}\n"
    template = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
  labels:
    app: {app}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {app}
  strategy:
    type: Recreate
  template:
    metadata:
      labels:
        app: {app}
    spec:
      containers:
      - name: {name}
        image: {docker_image}
        command: ["./pdr"]
        args:
{run_command_args}
        resources:
          requests:
            memory: {memory}
            cpu: {cpu}
        env:
          - name: PRIVATE_KEY
            value: {private_key}
          - name: PRIVATE_KEY2
            value: {private_key_2}
      restartPolicy: Always
    """
    return template
