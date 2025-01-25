from dataclasses import dataclass
from typing import List, Optional
from pdr_backend.deployer.util.models.SingleAgentConfig import SingleAgentConfig


# pylint: disable=too-many-instance-attributes
@dataclass
class AgentsDeployConfig:
    agents: List[SingleAgentConfig]
    type: str
    memory: Optional[str]
    cpu: Optional[str]
    approach: Optional[int] = None
    pdr_backend_image_source: Optional[str] = None
    source: Optional[str] = None
    network: Optional[str] = None
    s_until_epoch_end: Optional[int] = None
