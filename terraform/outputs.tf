# outputs.tf
# Outputs generated after Terraform provisioning.

output "repository_url" {
  description = "The URL of the Artifact Registry repository."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.repo.repository_id}"
}

output "service_url" {
  description = "The public HTTPS URL of the deployed Cloud Run service."
  value       = google_cloud_run_v2_service.api.uri
}

output "image_tag_instructions" {
  description = "How to tag and push your local Docker image to this registry."
  value       = "docker tag fraud-detection-api:latest ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.repo.repository_id}/${var.service_name}:latest"
}

output "docker_push_instructions" {
  description = "How to push your local Docker image to this registry."
  value       = "docker push ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.repo.repository_id}/${var.service_name}:latest"
}
