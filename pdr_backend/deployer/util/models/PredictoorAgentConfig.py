from dataclasses import dataclass
from typing import Optional

from pdr_backend.deployer.util.models.AgentDeployConfig import AgentsDeployConfig

from pdr_backend.deployer.util.models.SingleAgentConfig import SingleAgentConfig


@dataclass
class PredictoorAgentConfig(SingleAgentConfig):
    pair: str
    timeframe: str
    stake_amt: int
    approach: Optional[int] = None
    source: Optional[str] = None
    cpu: Optional[str] = None
    memory: Optional[str] = None
    private_key: Optional[str] = None
    network: Optional[str] = None
    s_until_epoch_end: Optional[int] = None

    def update_with_defaults(self, defaults: AgentsDeployConfig):
        for field in defaults.__dict__:
            if getattr(self, field, None) is None:
                setattr(self, field, getattr(defaults, field))
        # raise an error if any required fields are still None
        for field in self.__dict__:
            if getattr(self, field, None) is None and field not in [
                "private_key",
                "cpu",
                "memory",
            ]:
                raise ValueError(f"Field {field} is required but is not set")

    def get_run_command(
        self, stake_amt, approach, full_pair_name, network, s_until_epoch_end, yaml_path
    ):
        lake_feed_name = full_pair_name.replace(" c", "")
        override_feed = [
            f'--predictoor_ss.predict_feed={full_pair_name}',
            f"--predictoor_ss.aimodel_ss.input_feeds=[\"{full_pair_name}\"]",
            f"--lake_ss.feeds=[\"{lake_feed_name}\"]",
        ]
        override_stake = [f"--predictoor_ss.bot_only.stake_amount={stake_amt}"]
        override_s_until = [
            f"--predictoor_ss.bot_only.s_until_epoch_end={s_until_epoch_end}"
        ]

        return (
            [f"pdr", "predictoor", f"\"{approach}\"", yaml_path, network]
            + override_feed
            + override_stake
            + override_s_until
        )
