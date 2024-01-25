from dataclasses import dataclass
from typing import List, Optional
from deployer.models.SingleAgentConfig import SingleAgentConfig


@dataclass
class AgentsDeployConfig:
    cpu: str
    memory: str
    agents: List[SingleAgentConfig]
    type: str
    approach: Optional[int] = None
    pdr_backend_image_source: Optional[str] = None
    source: Optional[str] = None
    network: Optional[str] = None
    s_until_epoch_end: Optional[int] = None
