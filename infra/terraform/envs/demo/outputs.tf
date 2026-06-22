output "aws_region" {
  value = var.aws_region
}

output "cluster_name" {
  value = aws_eks_cluster.this.name
}

output "cluster_endpoint" {
  value = aws_eks_cluster.this.endpoint
}

output "ecr_repository_url" {
  value = aws_ecr_repository.worker.repository_url
}

output "worker_image_uri" {
  value = local.worker_image
}

output "temporal_frontend_service" {
  value = "temporal-frontend.${local.temporal_namespace}.svc.cluster.local:7233"
}

output "rds_endpoint" {
  value = aws_db_instance.temporal.address
}

output "control_plane_subnet_ids" {
  value = local.control_plane_subnet_ids
}

output "vpc_cidr_block" {
  value = data.aws_vpc.default.cidr_block
}

output "temporal_ui_enabled" {
  value = var.temporal_ui_enabled
}

output "temporal_team_role_arn" {
  description = "Role team members assume for Temporal UI tunneling and cluster-admin kubectl."
  value       = one(aws_iam_role.team[*].arn)
}

output "temporal_ui_bastion_instance_id" {
  description = "SSM bastion the Temporal UI tunnel targets."
  value       = one(aws_instance.bastion[*].id)
}
