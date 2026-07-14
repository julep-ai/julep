variable "aws_region" {
  type        = string
  description = "AWS region for all resources."
  default     = "us-east-1"
}

variable "name_prefix" {
  type        = string
  description = "Prefix used for AWS and Kubernetes resource names."
  default     = "julep-v2-temporal-demo"

  validation {
    condition = (
      length(var.name_prefix) <= 63 - length("-releases-") - 12
      && can(regex("^[a-z](?:[a-z0-9-]*[a-z0-9])?$", var.name_prefix))
      && !strcontains(var.name_prefix, "--")
    )
    error_message = "name_prefix must be 1-41 lowercase characters, start with a letter, contain only letters, digits, or single hyphens, and not end with a hyphen; this keeps <name_prefix>-releases-<12-digit-account-id> within the 63-character S3 bucket limit."
  }
}

variable "kubernetes_version" {
  type        = string
  description = "EKS Kubernetes version."
  default     = "1.33"
}

variable "vpc_id" {
  type        = string
  description = "Existing VPC that contains every EKS and Temporal subnet."

  validation {
    condition     = can(regex("^vpc-[0-9a-f]+$", var.vpc_id))
    error_message = "vpc_id must be an AWS VPC ID such as vpc-0123456789abcdef0."
  }
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "Existing private subnet IDs for EKS, Temporal RDS, internal load balancers, and the SSM bastion. Supply at least two subnets in distinct Availability Zones."

  validation {
    condition = (
      length(var.private_subnet_ids) >= 2
      && length(distinct(var.private_subnet_ids)) == length(var.private_subnet_ids)
      && alltrue([
        for subnet_id in var.private_subnet_ids :
        can(regex("^subnet-[0-9a-f]+$", subnet_id))
      ])
    )
    error_message = "private_subnet_ids must contain at least two distinct AWS subnet IDs."
  }
}

variable "allow_public_subnets_for_demo" {
  type        = bool
  description = "Explicit disposable-demo escape hatch for default-VPC subnets that auto-assign public IPs. Never enable in production."
  default     = false
}

variable "worker_image_tag" {
  type        = string
  description = "Tag used for the demo worker image."
  default     = "latest"
}

variable "cluster_endpoint_public_access" {
  type        = bool
  description = "Whether the EKS API is public. Production defaults to private-only."
  default     = false
}

variable "temporal_retention" {
  type        = string
  description = "Temporal workflow history retention for the application namespace."
  default     = "14d"
}

variable "rds_backup_retention_days" {
  type        = number
  description = "RDS automated backup retention."
  default     = 14
}

variable "rds_deletion_protection" {
  type        = bool
  description = "Protect the dedicated Temporal database from accidental deletion."
  default     = true
}

variable "rds_skip_final_snapshot" {
  type        = bool
  description = "Delete Temporal RDS without a final snapshot. This destructive opt-out is independent of deletion protection and is only intended for disposable demos."
  default     = false
}

variable "release_bucket_force_destroy" {
  type        = bool
  description = "Allow destroying a non-empty release CAS bucket. Keep false outside ephemeral demos."
  default     = false
}

variable "deploy_demo_worker" {
  type        = bool
  description = "Install the legacy single demo worker. Application lanes are normally reconciled by julep apply."
  default     = false
}

variable "temporal_payload_keyring" {
  type        = map(string)
  description = "AES-256-GCM keyring by key ID. Empty generates an initial v1 key; production supplies and retains explicit keys."
  sensitive   = true
  default     = {}

  validation {
    condition = alltrue([
      for key_id, key in var.temporal_payload_keyring :
      can(regex("^[A-Za-z0-9._-]+$", key_id)) && can(regex("^[0-9a-fA-F]{64}$", key))
    ])
    error_message = "Every payload key ID must use only letters, digits, dot, underscore, or hyphen, and every value must be exactly 64 hexadecimal characters."
  }
}

variable "temporal_payload_active_key_id" {
  type        = string
  description = "Active Temporal payload key ID; retain all older IDs through the history retention window."
  default     = "v1"

  validation {
    condition     = can(regex("^[A-Za-z0-9._-]+$", var.temporal_payload_active_key_id))
    error_message = "temporal_payload_active_key_id must use only letters, digits, dot, underscore, or hyphen."
  }
}

variable "secrets_recovery_window_days" {
  type        = number
  description = "Secrets Manager deletion recovery window. Production uses 30; disposable demos use 0 for immediate name reuse."
  default     = 30

  validation {
    condition = (
      var.secrets_recovery_window_days == 0
      || (
        var.secrets_recovery_window_days >= 7
        && var.secrets_recovery_window_days <= 30
      )
    )
    error_message = "secrets_recovery_window_days must be 0 or between 7 and 30."
  }
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
  description = "Maximum workers per release and the shared namespace-wide model-worker pod quota. Each worker is pinned to one concurrent activity, so this is also the global model concurrency ceiling across overlapping releases."
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
