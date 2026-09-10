# main.tf
# Terraform configuration to provision Artifact Registry and Cloud Run service for MLOps Fraud Detection.

terraform {
  required_version = ">= 1.0.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Enable Required Google Services/APIs
resource "google_project_service" "run" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "artifactregistry" {
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

# 2. Artifact Registry Repository to hold Docker Images
resource "google_artifact_registry_repository" "repo" {
  depends_on    = [google_project_service.artifactregistry]
  location      = var.region
  repository_id = var.repository_id
  description   = "Docker repository for MLOps Fraud Detection images"
  format        = "DOCKER"
}

# 3. Cloud Run Service (Serverless FastAPI deployment)
resource "google_cloud_run_v2_service" "api" {
  name     = var.service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      # Use a placeholder image initially or our built image if pushed.
      # Users can push their built image to this registry and update this container image tag.
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.repo.repository_id}/${var.service_name}:latest"
      
      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      ports {
        container_port = 8000
      }

      env {
        name  = "MODEL_VERSION"
        value = "1.0.0"
      }
      
      env {
        name  = "MODEL_DIR"
        value = "/app"
      }
    }
    
    scaling {
      max_instance_count = 5
      min_instance_count = 0  # Allow scale-to-zero when idle to minimize cost
    }
  }

  depends_on = [
    google_project_service.run,
    google_artifact_registry_repository.repo
  ]
}

# 4. Allow Unauthenticated Public Access
resource "google_cloud_run_v2_service_iam_member" "noauth" {
  location = google_cloud_run_v2_service.api.location
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
