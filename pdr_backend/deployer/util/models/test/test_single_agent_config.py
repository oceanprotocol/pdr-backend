from pdr_backend.deployer.util.models.SingleAgentConfig import SingleAgentConfig


def test_single_agent_config_initialization():
    private_key = "0x1"
    config = SingleAgentConfig(private_key=private_key)
    assert (
        config.private_key == private_key
    ), "Private key should be set correctly on initialization."


def test_set_private_key():
    config = SingleAgentConfig(private_key="initial_key")
    new_private_key = "new_private_key"
    config.set_private_key(new_private_key)
    assert (
        config.private_key == new_private_key
    ), "set_private_key should update the private key."
