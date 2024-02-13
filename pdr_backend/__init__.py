import logging
import logging.config
import yaml


with open("logging.yaml", "rt") as f:
    # todo: add custom logging.yaml e.g. mylogging.yaml similar to ppss.yaml
    config = yaml.safe_load(f.read())
    logging.config.dictConfig(config)
