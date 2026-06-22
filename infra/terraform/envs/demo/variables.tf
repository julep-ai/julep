variable "aws_region" {
  type        = string
  description = "AWS region for all resources."
  default     = "us-east-1"
}

variable "name_prefix" {
  type        = string
  description = "Prefix used for AWS and Kubernetes resource names."
  default     = "julep-v2-temporal-demo"
}

variable "kubernetes_version" {
  type        = string
  description = "EKS Kubernetes version."
  default     = "1.33"
}

variable "unsupported_control_plane_azs" {
  type        = set(string)
  description = "AZs to exclude from EKS control-plane subnet selection."
  default     = ["us-east-1e"]
}

variable "worker_image_tag" {
  type        = string
  description = "Tag used for the demo worker image."
  default     = "latest"
}

variable "temporal_chart_version" {
  type        = string
  description = "Temporal Helm chart version."
  default     = "1.2.0"
}

variable "keda_chart_version" {
  type        = string
  description = "KEDA Helm chart version."
  default     = "2.20.1"
}

variable "db_instance_class" {
  type        = string
  description = "RDS PostgreSQL instance class."
  default     = "db.t4g.micro"
}

variable "db_engine_version" {
  type        = string
  description = "RDS PostgreSQL engine version."
  default     = "16.6"
}

variable "db_allocated_storage_gb" {
  type        = number
  description = "Allocated RDS storage in GiB."
  default     = 20
}

variable "db_multi_az" {
  type        = bool
  description = "Whether to run RDS PostgreSQL as Multi-AZ."
  default     = false
}

variable "temporal_history_shards" {
  type        = number
  description = "Temporal history shard count. Cannot be changed after initial schema creation."
  default     = 4
}

variable "worker_min_replicas" {
  type        = number
  description = "Minimum worker replicas controlled by KEDA."
  default     = 0
}

variable "worker_max_replicas" {
  type        = number
  description = "Maximum worker replicas controlled by KEDA."
  default     = 4
}

variable "temporal_ui_enabled" {
  type        = bool
  description = "Provision the internal-ALB + SSM-bastion Temporal UI access stack."
  default     = true
}

variable "team_principal_arns" {
  type        = list(string)
  description = "IAM principal ARNs (users/roles) allowed to assume the temporal-team role for Temporal UI and cluster-admin access. Empty disables the team-access stack."
  default     = []
}

variable "bastion_instance_type" {
  type        = string
  description = "Instance type for the SSM tunnel bastion (arm64)."
  default     = "t4g.nano"
}
