from enforce_typing import enforce_types

from pdr_backend.predictoor.predictoor_agent import PredictoorAgent
from pdr_backend.predictoor.predictoor_config import PredictoorConfig


@enforce_types
class PredictoorConfig1(PredictoorConfig):
    def __init__(self):
        super().__init__()
        self.get_prediction = get_prediction

@enforce_types
class PredictoorAgent1(PredictoorAgent):
    
    def get_prediction(self, feed: dict, timestamp: str) -> Tuple[bool, int]:
        """Random prediction"""
        addr = feed["address"]        
        print(
            f" We were asked to predict {feed['name']} "
            f"(contract: {addr}) value "
            f"at estimated timestamp: {timestamp}"
        )

        # Pick random prediction & random stake. You need to customize this.
        import random
        predval = bool(random.getrandbits(1))
        stake = random.randint(10, 1000)

        print(f"Predicted {predval} with stake {stake}")
        return (predval, stake)


@enforce_types
def main():
    config = PredictoorConfig1()
    p = PredictoorAgent1(config)
    p.run()

if __name__ == "__main__":
    main()
