# variables.tf
# Variable declarations for GCP Infrastructure provisioning.

variable "project_id" {
  description = "The Google Cloud Project ID to deploy resources to."
  type        = string
}

variable "region" {
  description = "The Google Cloud region to deploy resources in."
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "The name of the Google Cloud Run service."
  type        = string
  default     = "fraud-detection-api"
}

variable "repository_id" {
  description = "The ID of the Artifact Registry repository."
  type        = string
  default     = "mlops-images"
}
