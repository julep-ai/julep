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
