from pdr_backend.deployer.util.models.PredictoorAgentConfig import PredictoorAgentConfig


def test_predictoor_agent_config():
    agent_config = PredictoorAgentConfig(
        private_key="0x1",
        pair="BTC/USDT",
        timeframe="5m",
        stake_amt=100,
        approach=1,
        source="binance",
        cpu="1",
        memory="2",
        network="mainnet",
        s_until_epoch_end=60,
    )

    assert isinstance(agent_config, PredictoorAgentConfig)
    assert agent_config.pair == "BTC/USDT"
    assert agent_config.timeframe == "5m"
    assert agent_config.stake_amt == 100
    assert agent_config.approach == 1
    assert agent_config.source == "binance"
    assert agent_config.cpu == "1"
    assert agent_config.memory == "2"
    assert agent_config.network == "mainnet"
    assert agent_config.s_until_epoch_end == 60
    assert agent_config.private_key == "0x1"
