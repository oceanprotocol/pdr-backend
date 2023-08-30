from enforce_typing import enforce_types

from pdr_backend.predictoor.predictoor_agent import PredictoorAgent

@enforce_types
class PredictoorAgent1(PredictoorAgent):
    
    def get_prediction(self, addr: str, timestamp: str) -> Tuple[bool, int]:
        """Random prediction"""
        feed_name = self.feeds[addr]["name"]
        print(f"Predict {feed_name} (addr={addr}) at timestamp {timestamp}")

        # Pick random prediction & random stake. You need to customize this.
        import random
        predval = bool(random.getrandbits(1))
        stake = random.randint(10, 1000)

        print(f"Predicted {predval} with stake {stake}")
        return (predval, stake)

