import json
import os
from pdr_backend.deployer.util.models.DeploymentInfo import DeploymentInfo

sample_data = {
    "config": {"key": "value"},
    "foldername": "test_folder",
    "config_name": "test_config",
    "deployment_method": "k8s",
    "ts_created": 42,
    "deployment_names": ["deploy1", "deploy2"],
}


def test_write_and_read(tmp_path):
    deployment_info = DeploymentInfo(**sample_data)
    file_path = tmp_path / "test_folder"
    file_path.mkdir()
    deployment_info.write(file_path)

    written_file_path = file_path / f"{sample_data['config_name']}.json"
    assert written_file_path.exists()

    read_deployment_info = DeploymentInfo.read(file_path, sample_data["config_name"])

    # verify attributes
    assert read_deployment_info.config == sample_data["config"]
    assert read_deployment_info.foldername == sample_data["foldername"]
    assert read_deployment_info.config_name == sample_data["config_name"]
    assert read_deployment_info.deployment_method == sample_data["deployment_method"]
    assert read_deployment_info.ts_created == sample_data["ts_created"]
    assert read_deployment_info.deployment_names == sample_data["deployment_names"]


def test_from_json(tmp_path):
    file_path = tmp_path / "test_config.json"
    with open(file_path, "w") as f:
        json.dump(sample_data, f)

    deployment_info = DeploymentInfo.from_json(file_path)

    # verify attributes
    assert deployment_info.config == sample_data["config"]
    assert deployment_info.foldername == sample_data["foldername"]
    assert deployment_info.config_name == sample_data["config_name"]
    assert deployment_info.deployment_method == sample_data["deployment_method"]
    assert deployment_info.ts_created == sample_data["ts_created"]
    assert deployment_info.deployment_names == sample_data["deployment_names"]
