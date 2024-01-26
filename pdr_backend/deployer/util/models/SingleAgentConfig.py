from dataclasses import dataclass


@dataclass
class SingleAgentConfig:
    def set_private_key(self, private_key):
        self.private_key = private_key
