from unittest.mock import patch
from pdr_backend.deployer.util.cloud import GCPProvider, AWSProvider, AzureProvider


@patch("pdr_backend.deployer.util.cloud.run_command")
def test_gcp_provider(mock_run_command):
    gcp = GCPProvider("zone", "project_id")
    gcp.create_container_registry("registry_name")
    mock_run_command.assert_called()


@patch("pdr_backend.deployer.util.cloud.run_command")
def test_aws_provider(mock_run_command):
    aws = AWSProvider("region")
    aws.create_container_registry("registry_name")
    mock_run_command.assert_called()


@patch("pdr_backend.deployer.util.cloud.run_command")
def test_azure_provider(mock_run_command):
    azure = AzureProvider("subscription_id", "resource_group")
    azure.create_container_registry("registry_name")
    mock_run_command.assert_called()
