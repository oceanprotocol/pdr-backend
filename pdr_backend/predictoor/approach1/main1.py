from enforce_typing import enforce_types

from pdr_backend.predictoor.approach1.predictoor_agent1 import PredictoorAgent1


@enforce_types
def do_main1():
    config = PredictoorAgent1.predictoor_config_class()
    p = PredictoorAgent1(config)
    p.run()


if __name__ == "__main__":
    do_main1()
