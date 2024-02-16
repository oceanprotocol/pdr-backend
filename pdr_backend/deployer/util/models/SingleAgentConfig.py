from dataclasses import dataclass


@dataclass
class SingleAgentConfig:
    private_key: str

    def set_private_key(self, private_key):
        # disable: attribute-defined-outside-init
        self.private_key = private_key
