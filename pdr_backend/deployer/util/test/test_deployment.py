# pylint: disable=redefined-outer-name, unused-argument
from unittest.mock import Mock, patch
from unittest.mock import MagicMock
import pytest
from pdr_backend.deployer.util import deployment


@pytest.fixture
def mock_shutil_which():
    with patch("shutil.which", return_value=True) as mock_which:
        yield mock_which


def test_check_cloud_provider_requirements(mock_shutil_which):
    deployment.check_cloud_provider_requirements("gcp")
    mock_shutil_which.assert_any_call("kubectl")
    mock_shutil_which.assert_any_call("gcloud")
    mock_shutil_which.assert_any_call("gke-gcloud-auth-plugin")


def test_check_image_build_requirements(mock_shutil_which):
    deployment.check_image_build_requirements()
    mock_shutil_which.assert_called_once_with("docker")


def test_build_image():
    with patch("pdr_backend.deployer.util.deployment.run_command") as mock_run_command:
        deployment.build_image("image_name", "image_tag")
        mock_run_command.assert_called_once_with(
            "docker build -t image_name:image_tag ."
        )


def test_push_image():
    with patch("pdr_backend.deployer.util.deployment.run_command") as mock_run_command:
        deployment.push_image("image_name", "image_tag", "registry_name")
        mock_run_command.assert_any_call(
            "docker tag image_name:image_tag registry_name/image_name:image_tag"
        )
        mock_run_command.assert_any_call(
            "docker push registry_name/image_name:image_tag"
        )


def test_deploy_agents_to_k8s():
    with patch("pdr_backend.deployer.util.deployment.run_command") as mock_run_command:
        deployment.deploy_agents_to_k8s("config_folder", "config_name")
        mock_run_command.assert_any_call(
            "kubectl create namespace config-name", False
        )  # sanitizes name _ => -
        mock_run_command.assert_any_call(
            "kubectl apply -f config_folder/ -n config-name"
        )


def test_deploy_cluster(mock_shutil_which):
    mock_provider = Mock()
    mock_provider.cluster_exists.return_value = False
    deployment.deploy_cluster(mock_provider, "cluster_name")
    mock_provider.create_kubernetes_cluster.assert_called_once_with("cluster-name")


def test_create_namespace(mock_shutil_which):
    with patch("pdr_backend.deployer.util.deployment.run_command") as mock_run_command:
        deployment.create_namespace("namespace")
        mock_run_command.assert_called_once_with(
            "kubectl create namespace namespace", False
        )


def test_destroy_cluster(mock_shutil_which):
    mock_provider = Mock()
    mock_provider.cluster_exists.return_value = True
    with patch("builtins.input", return_value="y"):
        deployment.destroy_cluster(mock_provider, "cluster_name", "config_name")
        mock_provider.delete_kubernetes_cluster.assert_called_once_with("cluster-name")


def test_destroy_cluster_pods(mock_shutil_which):
    mock_provider = Mock()
    mock_provider.cluster_exists.return_value = True
    with patch("pdr_backend.deployer.util.deployment.run_command") as mock_run_command:
        with patch("builtins.input", return_value="n"):
            deployment.destroy_cluster(mock_provider, "cluster_name", "config_name")
            mock_run_command.assert_called_once_with(
                "kubectl delete pods --all -n config-name"
            )


def test_deploy_registry(mock_shutil_which):
    mock_provider = Mock()
    mock_provider.registry_exists.return_value = False
    deployment.deploy_registry(mock_provider, "registry_name")
    mock_provider.create_container_registry.assert_called_once_with("registry-name")
    mock_provider.print_registry_url.assert_called_once_with("registry-name")
    mock_provider.auth_registry.assert_called_once_with("registry-name")


def test_delete_registry(mock_shutil_which):
    mock_provider = Mock()
    mock_provider.registry_exists.return_value = True
    deployment.delete_registry(mock_provider, "registry_name")
    mock_provider.delete_registry.assert_called_once_with("registry-name")


def test_delete_all_pods(mock_shutil_which):
    mock_provider = Mock()
    mock_provider.cluster_exists.return_value = True
    with patch("pdr_backend.deployer.util.deployment.run_command") as mock_run_command:
        deployment.delete_all_pods(mock_provider, "cluster_name", "config_name")
        mock_run_command.assert_called_once_with(
            "kubectl delete pods --all -n config-name"
        )


def test_cluster_logs(mock_shutil_which):
    mock_provider = Mock()
    mock_provider.cluster_exists.return_value = True
    with patch("pdr_backend.deployer.util.deployment.run_command") as mock_run_command:
        deployment.cluster_logs(
            mock_provider, "cluster_name", "app_name", "config_name"
        )
        mock_run_command.assert_any_call("kubectl get pods -n config-name")
        mock_run_command.assert_any_call(
            "kubectl logs -l app=app_name -f -n config-name"
        )


def test_deploy_config(mock_shutil_which):
    mock_provider = Mock()
    mock_provider.json = {"type": "gcp"}
    mock_deployment_info = MagicMock()
    mock_deployment_info.deployment_method = "k8s"
    mock_deployment_info.config_name = "config_name"
    mock_deployment_info.foldername = "foldername"
    with patch(
        "pdr_backend.deployer.util.deployment.DeploymentInfo.read",
        return_value=mock_deployment_info,
    ):
        with patch(
            "pdr_backend.deployer.util.deployment.deploy_cluster"
        ) as mock_deploy_cluster:
            with patch(
                "pdr_backend.deployer.util.deployment.deploy_agents_to_k8s"
            ) as mock_deploy_agents_to_k8s:
                deployment.deploy_config("config_file", mock_provider)
                mock_deploy_cluster.assert_called_once_with(
                    mock_provider, "config_name"
                )
                mock_deploy_agents_to_k8s.assert_called_once_with(
                    "foldername", "config_name"
                )


def test_destroy_config(mock_shutil_which):
    mock_provider = Mock()
    mock_provider.json = {"type": "gcp"}
    mock_deployment_info = Mock()
    mock_deployment_info.deployment_method = "k8s"
    mock_deployment_info.config_name = "config_name"
    with patch(
        "pdr_backend.deployer.util.deployment.DeploymentInfo.read",
        return_value=mock_deployment_info,
    ):
        with patch(
            "pdr_backend.deployer.util.deployment.destroy_cluster"
        ) as mock_destroy_cluster:
            deployment.destroy_config("config_file", mock_provider)
            mock_destroy_cluster.assert_called_once_with(
                mock_provider, "config_name", "config_name"
            )


def test_logs_config(mock_shutil_which):
    mock_provider = Mock()
    mock_provider.json = {"type": "gcp"}
    mock_deployment_info = Mock()
    mock_deployment_info.deployment_method = "k8s"
    mock_deployment_info.config_name = "config_name"
    with patch(
        "pdr_backend.deployer.util.deployment.DeploymentInfo.read",
        return_value=mock_deployment_info,
    ):
        with patch(
            "pdr_backend.deployer.util.deployment.cluster_logs"
        ) as mock_cluster_logs:
            deployment.logs_config("config_file", mock_provider)
            mock_cluster_logs.assert_called_once_with(
                mock_provider, "config_name", "pdr-predictoor", "config_name"
            )
