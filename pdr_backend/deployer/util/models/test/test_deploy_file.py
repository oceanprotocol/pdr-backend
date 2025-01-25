import os
from pdr_backend.deployer.util.models.DeployFile import DeployFile
from pdr_backend.deployer.util.models.DeploymentMethod import DeploymentMethod


def test_write_creates_file_with_correct_content(tmp_path):
    method = DeploymentMethod.K8S
    content = "Test content"
    name = "test/file.txt"
    deploy_file = DeployFile(method=method, content=content, name=name)

    deploy_file.write(tmp_path)

    # Verify
    expected_file_path = tmp_path / "test-file.txt"
    assert os.path.exists(expected_file_path), "File was not created"
    with open(expected_file_path, "r", encoding="utf-8") as f:
        file_content = f.read()
    assert file_content == content, "File content does not match"


def test_write_handles_slash_in_name_correctly(tmp_path):
    method = DeploymentMethod.K8S
    content = "Another test content"
    name = "another/test/file.txt"
    deploy_file = DeployFile(method=method, content=content, name=name)

    deploy_file.write(tmp_path)

    # Verify
    expected_file_path = tmp_path / "another-test-file.txt"
    assert os.path.exists(
        expected_file_path
    ), "File was not created with slashes replaced"
