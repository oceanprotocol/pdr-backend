from enforce_typing import enforce_types

from pdr_backend.predictoor.approach1.predictoor_agent1 import PredictoorAgent1
from pdr_backend.predictoor.approach1.predictoor_config1 import PredictoorConfig1


@enforce_types
def do_main1():
    config = PredictoorConfig1()
    p = PredictoorAgent1(config)
    p.run()


if __name__ == "__main__":
    do_main1()
