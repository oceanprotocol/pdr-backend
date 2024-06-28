#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
import logging.config
import os
import yaml


logging_config_path = (
    "my_logging.yaml" if os.path.exists("my_logging.yaml") else "logging.yaml"
)

with open(logging_config_path, "rt") as f:
    config = yaml.safe_load(f.read())
    logging.config.dictConfig(config)
