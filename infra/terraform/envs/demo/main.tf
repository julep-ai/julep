locals {
  tags = {
    Project = "julep-v2"
    Stack   = var.name_prefix
  }

  control_plane_subnet_ids = [
    for subnet in data.aws_subnet.default :
    subnet.id if !contains(var.unsupported_control_plane_azs, subnet.availability_zone)
  ]

  temporal_db_secret_name = "temporal-db"
  temporal_namespace      = "temporal"
  worker_namespace        = "julep-demo"
  worker_task_queue       = "composable-agents"
  worker_image            = "${aws_ecr_repository.worker.repository_url}:${var.worker_image_tag}"
}

data "aws_caller_identity" "current" {}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_subnet" "default" {
  for_each = toset(data.aws_subnets.default.ids)
  id       = each.value
}

data "aws_eks_cluster_auth" "this" {
  name       = aws_eks_cluster.this.name
  depends_on = [aws_eks_cluster.this]
}

resource "aws_iam_role" "cluster" {
  name = "${var.name_prefix}-cluster"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "eks.amazonaws.com"
      }
      Action = [
        "sts:AssumeRole",
        "sts:TagSession",
      ]
    }]
  })
}

resource "aws_iam_role_policy_attachment" "cluster" {
  for_each = toset([
    "AmazonEKSClusterPolicy",
    "AmazonEKSComputePolicy",
    "AmazonEKSBlockStoragePolicy",
    "AmazonEKSLoadBalancingPolicy",
    "AmazonEKSNetworkingPolicy",
  ])

  role       = aws_iam_role.cluster.name
  policy_arn = "arn:aws:iam::aws:policy/${each.value}"
}

resource "aws_iam_role" "node" {
  name = "${var.name_prefix}-node"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "node" {
  for_each = toset([
    "AmazonEKSWorkerNodeMinimalPolicy",
    "AmazonEC2ContainerRegistryPullOnly",
  ])

  role       = aws_iam_role.node.name
  policy_arn = "arn:aws:iam::aws:policy/${each.value}"
}

resource "aws_ecr_repository" "worker" {
  name         = "${var.name_prefix}-worker"
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_eks_cluster" "this" {
  name                          = var.name_prefix
  role_arn                      = aws_iam_role.cluster.arn
  version                       = var.kubernetes_version
  bootstrap_self_managed_addons = false

  access_config {
    authentication_mode                         = "API"
    bootstrap_cluster_creator_admin_permissions = true
  }

  vpc_config {
    subnet_ids              = local.control_plane_subnet_ids
    endpoint_public_access  = true
    endpoint_private_access = true
  }

  compute_config {
    enabled       = true
    node_pools    = ["general-purpose", "system"]
    node_role_arn = aws_iam_role.node.arn
  }

  kubernetes_network_config {
    elastic_load_balancing {
      enabled = true
    }
  }

  storage_config {
    block_storage {
      enabled = true
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.cluster,
    aws_iam_role_policy_attachment.node,
  ]
}

resource "random_password" "temporal_db" {
  length  = 24
  special = false
}

resource "aws_db_subnet_group" "temporal" {
  name       = "${var.name_prefix}-db"
  subnet_ids = local.control_plane_subnet_ids
}

resource "aws_security_group" "temporal_db" {
  name        = "${var.name_prefix}-db"
  description = "RDS access for ${var.name_prefix}"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "PostgreSQL from default VPC"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.default.cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "temporal" {
  identifier              = var.name_prefix
  engine                  = "postgres"
  engine_version          = var.db_engine_version
  instance_class          = var.db_instance_class
  allocated_storage       = var.db_allocated_storage_gb
  max_allocated_storage   = max(var.db_allocated_storage_gb, 100)
  storage_type            = "gp3"
  storage_encrypted       = true
  username                = "temporal"
  password                = random_password.temporal_db.result
  db_subnet_group_name    = aws_db_subnet_group.temporal.name
  vpc_security_group_ids  = [aws_security_group.temporal_db.id]
  publicly_accessible     = false
  multi_az                = var.db_multi_az
  backup_retention_period = 1
  deletion_protection     = false
  skip_final_snapshot     = true
  apply_immediately       = true
}

resource "kubernetes_namespace_v1" "temporal" {
  metadata {
    name = local.temporal_namespace
  }

  depends_on = [aws_eks_cluster.this]
}

resource "kubernetes_namespace_v1" "keda" {
  metadata {
    name = "keda"
  }

  depends_on = [aws_eks_cluster.this]
}

resource "kubernetes_namespace_v1" "worker" {
  metadata {
    name = local.worker_namespace
  }

  depends_on = [aws_eks_cluster.this]
}

resource "kubernetes_secret_v1" "temporal_db" {
  metadata {
    name      = local.temporal_db_secret_name
    namespace = kubernetes_namespace_v1.temporal.metadata[0].name
  }

  data = {
    password = random_password.temporal_db.result
  }

  type = "Opaque"
}

resource "kubernetes_storage_class_v1" "auto_ebs" {
  metadata {
    name = "auto-ebs-sc"

    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "true"
    }
  }

  storage_provisioner    = "ebs.csi.eks.amazonaws.com"
  volume_binding_mode    = "WaitForFirstConsumer"
  allow_volume_expansion = true

  parameters = {
    type      = "gp3"
    encrypted = "true"
  }

  allowed_topologies {
    match_label_expressions {
      key    = "eks.amazonaws.com/compute-type"
      values = ["auto"]
    }
  }
}

resource "helm_release" "keda" {
  name       = "keda"
  repository = "https://kedacore.github.io/charts"
  chart      = "keda"
  version    = var.keda_chart_version
  namespace  = kubernetes_namespace_v1.keda.metadata[0].name

  wait    = true
  timeout = 600
}

resource "helm_release" "temporal" {
  name       = "temporal"
  repository = "https://go.temporal.io/helm-charts"
  chart      = "temporal"
  version    = var.temporal_chart_version
  namespace  = kubernetes_namespace_v1.temporal.metadata[0].name

  values = [
    yamlencode({
      server = {
        replicaCount = 1
        config = {
          logLevel = "info"
          persistence = {
            numHistoryShards = var.temporal_history_shards
            datastores = {
              default = {
                sql = {
                  createDatabase  = true
                  manageSchema    = true
                  pluginName      = "postgres12"
                  driverName      = "postgres12"
                  databaseName    = "temporal"
                  connectAddr     = "${aws_db_instance.temporal.address}:5432"
                  connectProtocol = "tcp"
                  user            = aws_db_instance.temporal.username
                  existingSecret  = kubernetes_secret_v1.temporal_db.metadata[0].name
                  secretKey       = "password"
                  maxConns        = 20
                  maxIdleConns    = 20
                  connectAttributes = {
                    sslmode = "require"
                  }
                }
              }
              visibility = {
                sql = {
                  createDatabase  = true
                  manageSchema    = true
                  pluginName      = "postgres12"
                  driverName      = "postgres12"
                  databaseName    = "temporal_visibility"
                  connectAddr     = "${aws_db_instance.temporal.address}:5432"
                  connectProtocol = "tcp"
                  user            = aws_db_instance.temporal.username
                  existingSecret  = kubernetes_secret_v1.temporal_db.metadata[0].name
                  secretKey       = "password"
                  maxConns        = 20
                  maxIdleConns    = 20
                  connectAttributes = {
                    sslmode = "require"
                  }
                }
              }
            }
          }
          namespaces = {
            create = true
            namespace = [{
              name      = "default"
              retention = "3d"
            }]
          }
        }
      }
      web = {
        enabled = true
      }
      admintools = {
        enabled = true
      }
    })
  ]

  wait    = true
  timeout = 900

  depends_on = [
    aws_db_instance.temporal,
    kubernetes_secret_v1.temporal_db,
  ]
}

resource "helm_release" "worker" {
  name      = "ca-worker"
  chart     = "${path.module}/../../../helm/ca-worker"
  namespace = kubernetes_namespace_v1.worker.metadata[0].name

  values = [
    yamlencode({
      image = {
        repository = aws_ecr_repository.worker.repository_url
        tag        = var.worker_image_tag
        pullPolicy = "IfNotPresent"
      }
      temporal = {
        address   = "temporal-frontend.${local.temporal_namespace}.svc.cluster.local:7233"
        namespace = "default"
        taskQueue = local.worker_task_queue
      }
      worker = {
        gracefulShutdownSeconds = 20
        healthPort              = 8080
        secretName              = "llm-keys"
      }
      scaling = {
        minReplicas               = var.worker_min_replicas
        maxReplicas               = var.worker_max_replicas
        pollingInterval           = 5
        cooldownPeriod            = 60
        targetQueueSize           = "1"
        activationTargetQueueSize = "0"
      }
      resources = {
        requests = {
          cpu    = "250m"
          memory = "512Mi"
        }
      }
    })
  ]

  wait    = true
  timeout = 300

  depends_on = [
    helm_release.keda,
    helm_release.temporal,
  ]
}
