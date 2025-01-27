import pytest
from pdr_backend.deployer.util.models.DeploymentMethod import DeploymentMethod


def test_str_method():
    assert str(DeploymentMethod.K8S) == "k8s"


def test_extension_property_valid():
    assert DeploymentMethod.K8S.extension == "yaml"


def test_extension_property_invalid():
    with pytest.raises(ValueError) as err:
        DeploymentMethod("invalid")
    assert "'invalid' is not a valid DeploymentMethod" in str(err.value)


def test_from_str_valid():
    assert DeploymentMethod.from_str("k8s") == DeploymentMethod.K8S


def test_from_str_invalid():
    with pytest.raises(ValueError) as excinfo:
        DeploymentMethod.from_str("invalid")
    assert "Invalid deployment method" in str(excinfo.value)


def test_deploy_command():
    config_name = "test-config"
    expected_command = f"pdr deployer deploy {config_name}"
    assert DeploymentMethod.K8S.deploy_command(config_name) == expected_command
