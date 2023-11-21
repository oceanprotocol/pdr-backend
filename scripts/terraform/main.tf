# Configure the cloud provider
provider "google" {
  credentials = file(var.credentials_path)  # Replace with your GCP credentials file
  project     = var.project_id             # Replace with your GCP project ID
  region      = var.region                    # Replace with your desired region
}

data "google_client_config" "current" {}

resource "google_container_cluster" "pdr_cluster" {
  name     = "pdr-cluster"
  location = var.zone

  remove_default_node_pool = true
  initial_node_count = 1

  master_auth {
    client_certificate_config {
      issue_client_certificate = false
    }
  }
}

resource "google_container_node_pool" "pdr_nodes" {
  name       = "pdr-nodes"
  location   = var.zone
  cluster    = google_container_cluster.pdr_cluster.name
  node_count = 1

  node_config {
    preemptible  = true
    machine_type = "e2-small"

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}

provider "kubernetes" {
  host                   = "https://${google_container_cluster.pdr_cluster.endpoint}"
  token                  = data.google_client_config.current.access_token
  cluster_ca_certificate = base64decode(google_container_cluster.pdr_cluster.master_auth[0].cluster_ca_certificate)
}

resource "kubernetes_deployment" "app_deployment" {
  metadata {
    name = "predictoor-agents"
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "predictoor-agents"
      }
    }

    template {
      metadata {
        labels = {
          app = "predictoor-agents"
        }
      }

      spec {
        container {
          image = "gcr.io/var.project_id/pdr-backend:latest"
          name  = "pdr-btc-5m"

          env {
            name = "PRIVATE_KEY"
            value = var.BTC_5m_PK
          }

          env {
            name = "MODULE_NAME"
            value = "predictoor"
          }

          env {
            name = "COMMAND"
            value = "3"
          }
        }

        container {
          image = "gcr.io/var.project_id/pdr-backend:latest"
          name  = "pdr-eth-5m"

          env {
            name = "PRIVATE_KEY"
            value = var.ETH_5m_PK
          }

          env {
            name = "MODULE_NAME"
            value = "predictoor"
          }

          env {
            name = "COMMAND"
            value = "3"
          }
        }
      }
    }
  }
}