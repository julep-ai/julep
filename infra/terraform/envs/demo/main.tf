locals {
  tags = {
    Project = "julep-v2"
    Stack   = var.name_prefix
  }

  private_subnet_ids = sort(var.private_subnet_ids)

  temporal_db_secret_name = "temporal-db"
  temporal_namespace      = "temporal"
  worker_namespace        = "julep-demo"
  worker_task_queue       = "julep"
  worker_image            = "${aws_ecr_repository.worker.repository_url}:${var.worker_image_tag}"
  release_bucket_name     = "${var.name_prefix}-releases-${data.aws_caller_identity.current.account_id}"
  rds_final_snapshot_identifier = var.rds_skip_final_snapshot ? null : format(
    "%s-final-%s",
    var.name_prefix,
    random_id.temporal_db_final_snapshot[0].hex,
  )
  temporal_payload_keyring = length(var.temporal_payload_keyring) == 0 ? {
    v1 = random_id.temporal_payload_key.hex
  } : var.temporal_payload_keyring
  temporal_payload_keyring_text = join(",", [
    for key_id in sort(keys(local.temporal_payload_keyring)) :
    "${key_id}=${local.temporal_payload_keyring[key_id]}"
  ])
}

check "temporal_payload_active_key" {
  assert {
    condition     = contains(keys(local.temporal_payload_keyring), var.temporal_payload_active_key_id)
    error_message = "temporal_payload_active_key_id must exist in temporal_payload_keyring."
  }
}

check "rds_final_snapshot_policy" {
  assert {
    condition     = !var.rds_skip_final_snapshot || !var.rds_deletion_protection
    error_message = "rds_skip_final_snapshot=true is only valid when rds_deletion_protection=false; production teardown should disable protection while retaining the default final snapshot."
  }

  assert {
    condition = var.rds_skip_final_snapshot ? true : (
      length(local.rds_final_snapshot_identifier) <= 255
      && can(regex(
        "^[A-Za-z](?:[A-Za-z0-9-]*[A-Za-z0-9])?$",
        local.rds_final_snapshot_identifier,
      ))
      && !strcontains(local.rds_final_snapshot_identifier, "--")
    )
    error_message = "The generated RDS final snapshot identifier is invalid."
  }
}

check "release_bucket_name" {
  assert {
    condition = (
      length(local.release_bucket_name) <= 63
      && can(regex("^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$", local.release_bucket_name))
      && !strcontains(local.release_bucket_name, "--")
    )
    error_message = "The derived S3 release bucket name is not DNS-compatible or exceeds 63 characters."
  }
}

data "aws_caller_identity" "current" {}

data "aws_vpc" "selected" {
  id = var.vpc_id
}

data "aws_subnet" "private" {
  for_each = toset(local.private_subnet_ids)
  id       = each.value
}

data "aws_route_table" "private" {
  for_each  = toset(local.private_subnet_ids)
  subnet_id = each.value
}

check "private_subnet_topology" {
  assert {
    condition = alltrue([
      for subnet in data.aws_subnet.private : subnet.vpc_id == var.vpc_id
    ])
    error_message = "Every private_subnet_ids entry must belong to vpc_id."
  }

  assert {
    condition = length(distinct([
      for subnet in data.aws_subnet.private : subnet.availability_zone
    ])) >= 2
    error_message = "private_subnet_ids must span at least two Availability Zones."
  }

  assert {
    condition = var.allow_public_subnets_for_demo || alltrue([
      for subnet in data.aws_subnet.private : !subnet.map_public_ip_on_launch
    ])
    error_message = "Production private_subnet_ids must not auto-assign public IPs. The disposable demo wrapper is the only supported caller of allow_public_subnets_for_demo=true."
  }

  assert {
    condition = var.allow_public_subnets_for_demo || alltrue([
      for route_table in data.aws_route_table.private : alltrue([
        for route in route_table.routes : !(
          (
            try(route.cidr_block, "") == "0.0.0.0/0"
            || try(route.ipv6_cidr_block, "") == "::/0"
          )
          && try(startswith(route.gateway_id, "igw-"), false)
        )
      ])
    ])
    error_message = "Production private_subnet_ids must not have a default route directly to an internet gateway. Use NAT or private VPC endpoints for egress."
  }
}

resource "aws_kms_key" "data" {
  description             = "Julep Temporal RDS, release CAS, and secrets encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true
}

resource "aws_kms_alias" "data" {
  name          = "alias/${var.name_prefix}-data"
  target_key_id = aws_kms_key.data.key_id
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

resource "aws_iam_role" "worker" {
  name = "${var.name_prefix}-worker"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "pods.eks.amazonaws.com"
      }
      Action = [
        "sts:AssumeRole",
        "sts:TagSession",
      ]
    }]
  })
}

resource "aws_iam_role_policy" "worker_release_store" {
  name = "release-store-read"
  role = aws_iam_role.worker.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = aws_s3_bucket.releases.arn
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject"]
        Resource = "${aws_s3_bucket.releases.arn}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["kms:Decrypt", "kms:DescribeKey"]
        Resource = aws_kms_key.data.arn
      },
    ]
  })
}

resource "aws_ecr_repository" "worker" {
  name         = "${var.name_prefix}-worker"
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.data.arn
  }
}

resource "aws_s3_bucket" "releases" {
  bucket        = local.release_bucket_name
  force_destroy = var.release_bucket_force_destroy
}

resource "aws_s3_bucket_versioning" "releases" {
  bucket = aws_s3_bucket.releases.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "releases" {
  bucket = aws_s3_bucket.releases.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.data.arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "releases" {
  bucket                  = aws_s3_bucket.releases.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
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
    subnet_ids              = local.private_subnet_ids
    endpoint_public_access  = var.cluster_endpoint_public_access
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

resource "random_id" "temporal_payload_key" {
  byte_length = 32
}

resource "random_id" "temporal_db_final_snapshot" {
  count       = var.rds_skip_final_snapshot ? 0 : 1
  byte_length = 8

  keepers = {
    database_identifier = var.name_prefix
  }
}

resource "aws_secretsmanager_secret" "temporal_db" {
  name                    = "${var.name_prefix}/temporal/database"
  kms_key_id              = aws_kms_key.data.arn
  recovery_window_in_days = var.secrets_recovery_window_days
}

resource "aws_secretsmanager_secret_version" "temporal_db" {
  secret_id = aws_secretsmanager_secret.temporal_db.id
  secret_string = jsonencode({
    username = "temporal"
    password = random_password.temporal_db.result
  })
}

data "aws_secretsmanager_secret_version" "temporal_db" {
  secret_id  = aws_secretsmanager_secret.temporal_db.id
  depends_on = [aws_secretsmanager_secret_version.temporal_db]
}

resource "aws_secretsmanager_secret" "temporal_payload" {
  name                    = "${var.name_prefix}/temporal/payload-codec"
  kms_key_id              = aws_kms_key.data.arn
  recovery_window_in_days = var.secrets_recovery_window_days
}

resource "aws_secretsmanager_secret_version" "temporal_payload" {
  secret_id = aws_secretsmanager_secret.temporal_payload.id
  secret_string = jsonencode({
    active_key_id = var.temporal_payload_active_key_id
    keyring       = local.temporal_payload_keyring_text
  })
}

data "aws_secretsmanager_secret_version" "temporal_payload" {
  secret_id  = aws_secretsmanager_secret.temporal_payload.id
  depends_on = [aws_secretsmanager_secret_version.temporal_payload]
}

resource "aws_db_subnet_group" "temporal" {
  name       = "${var.name_prefix}-db"
  subnet_ids = local.private_subnet_ids
}

resource "aws_security_group" "temporal_db" {
  name        = "${var.name_prefix}-db"
  description = "RDS access for ${var.name_prefix}"
  vpc_id      = data.aws_vpc.selected.id

  ingress {
    description     = "PostgreSQL from the EKS cluster security group"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_eks_cluster.this.vpc_config[0].cluster_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "temporal" {
  identifier                = var.name_prefix
  engine                    = "postgres"
  engine_version            = var.db_engine_version
  instance_class            = var.db_instance_class
  allocated_storage         = var.db_allocated_storage_gb
  max_allocated_storage     = max(var.db_allocated_storage_gb, 100)
  storage_type              = "gp3"
  storage_encrypted         = true
  kms_key_id                = aws_kms_key.data.arn
  username                  = "temporal"
  password                  = random_password.temporal_db.result
  db_subnet_group_name      = aws_db_subnet_group.temporal.name
  vpc_security_group_ids    = [aws_security_group.temporal_db.id]
  publicly_accessible       = false
  multi_az                  = var.db_multi_az
  backup_retention_period   = var.rds_backup_retention_days
  deletion_protection       = var.rds_deletion_protection
  skip_final_snapshot       = var.rds_skip_final_snapshot
  final_snapshot_identifier = local.rds_final_snapshot_identifier
  apply_immediately         = true
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

resource "kubernetes_priority_class_v1" "model_worker" {
  metadata {
    name = "julep-model-worker"
  }

  value          = 0
  global_default = false
  description    = "Julep model workers governed by the shared concurrency quota."
}

resource "kubernetes_resource_quota_v1" "worker_concurrency" {
  metadata {
    name      = "julep-model-worker-concurrency"
    namespace = kubernetes_namespace_v1.worker.metadata[0].name
  }

  spec {
    hard = {
      pods = tostring(var.worker_max_replicas)
    }

    scope_selector {
      match_expression {
        scope_name = "PriorityClass"
        operator   = "In"
        values     = [kubernetes_priority_class_v1.model_worker.metadata[0].name]
      }
    }
  }
}

resource "kubernetes_service_account_v1" "worker" {
  metadata {
    name      = "julep-worker"
    namespace = kubernetes_namespace_v1.worker.metadata[0].name
  }
}

resource "aws_eks_pod_identity_association" "worker" {
  cluster_name    = aws_eks_cluster.this.name
  namespace       = kubernetes_namespace_v1.worker.metadata[0].name
  service_account = kubernetes_service_account_v1.worker.metadata[0].name
  role_arn        = aws_iam_role.worker.arn

  depends_on = [aws_iam_role_policy.worker_release_store]
}

# Secrets Manager is the durable source. Terraform reads its current managed
# version and materializes it into the Kubernetes consumption seam. Rotation is
# additive and requires an apply plus a controlled worker rollout.
resource "kubernetes_secret_v1" "temporal_payload" {
  metadata {
    name      = "temporal-payload-codec"
    namespace = kubernetes_namespace_v1.worker.metadata[0].name
  }

  data = {
    active-key-id = jsondecode(data.aws_secretsmanager_secret_version.temporal_payload.secret_string).active_key_id
    keyring       = jsondecode(data.aws_secretsmanager_secret_version.temporal_payload.secret_string).keyring
  }

  type = "Opaque"
}

resource "kubernetes_secret_v1" "temporal_db" {
  metadata {
    name      = local.temporal_db_secret_name
    namespace = kubernetes_namespace_v1.temporal.metadata[0].name
  }

  data = {
    password = jsondecode(data.aws_secretsmanager_secret_version.temporal_db.secret_string).password
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
              retention = var.temporal_retention
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
  count     = var.deploy_demo_worker ? 1 : 0
  name      = "julep-worker"
  chart     = "${path.module}/../../../helm/julep-worker"
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
        contextFactory          = "llm_weather_agent:make_context"
        gracefulShutdownSeconds = 20
        healthPort              = 8080
        secretName              = "llm-keys"
        application             = "julep-demo"
        releaseHash             = "demo"
        deploymentRevision      = "demo"
        deploymentConfigHash    = "demo"
        lane                    = "demo"
        maxConcurrentActivities = 1
      }
      serviceAccount = {
        create = false
        name   = kubernetes_service_account_v1.worker.metadata[0].name
      }
      payloadEncryption = {
        enabled        = true
        secretName     = kubernetes_secret_v1.temporal_payload.metadata[0].name
        keyringKey     = "keyring"
        activeKeyIdKey = "active-key-id"
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
    kubernetes_secret_v1.temporal_payload,
    aws_eks_pod_identity_association.worker,
    kubernetes_resource_quota_v1.worker_concurrency,
  ]
}

# ---------------------------------------------------------------------------
# Temporal UI access
#
# The Temporal web UI (temporal-web Service) is exposed through an internal-scheme
# ALB (created via kubectl in scripts/eks-demo-up.sh, since EKS Auto Mode's ALB
# scheme/subnets live in the IngressClassParams CRD). The only network path into
# the VPC to reach that ALB is an SSM-managed bastion: team members assume the
# shared temporal-team role (cluster-admin via an EKS access entry) and tunnel
# through the bastion with `aws ssm start-session` port-forwarding. No public
# endpoint; the gate is IAM + SSM + internal ALB.
# ---------------------------------------------------------------------------

locals {
  # The whole access stack is a no-op unless enabled AND at least one team
  # principal is supplied (an assume-role policy with no principals is invalid).
  temporal_ui_access_enabled = var.temporal_ui_enabled && length(var.team_principal_arns) > 0 ? 1 : 0
}

# Tag the ALB subnets so EKS Auto Mode discovers them for internal load balancers.
resource "aws_ec2_tag" "internal_elb" {
  for_each    = var.temporal_ui_enabled ? toset(local.private_subnet_ids) : toset([])
  resource_id = each.value
  key         = "kubernetes.io/role/internal-elb"
  value       = "1"
}

# Shared role the team assumes for both Temporal UI tunneling and kubectl access.
data "aws_iam_policy_document" "team_assume" {
  count = local.temporal_ui_access_enabled

  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "AWS"
      identifiers = var.team_principal_arns
    }
  }
}

resource "aws_iam_role" "team" {
  count              = local.temporal_ui_access_enabled
  name               = "${var.name_prefix}-team"
  assume_role_policy = data.aws_iam_policy_document.team_assume[0].json
}

resource "aws_eks_access_entry" "team" {
  count         = local.temporal_ui_access_enabled
  cluster_name  = aws_eks_cluster.this.name
  principal_arn = aws_iam_role.team[0].arn
  type          = "STANDARD"
}

resource "aws_eks_access_policy_association" "team_admin" {
  count         = local.temporal_ui_access_enabled
  cluster_name  = aws_eks_cluster.this.name
  principal_arn = aws_iam_role.team[0].arn
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"

  access_scope {
    type = "cluster"
  }

  depends_on = [aws_eks_access_entry.team]
}

# SSM bastion: the only network path into the VPC to reach the internal ALB.
resource "aws_iam_role" "bastion" {
  count = local.temporal_ui_access_enabled
  name  = "${var.name_prefix}-bastion"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "bastion_ssm" {
  count      = local.temporal_ui_access_enabled
  role       = aws_iam_role.bastion[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "bastion" {
  count = local.temporal_ui_access_enabled
  name  = "${var.name_prefix}-bastion"
  role  = aws_iam_role.bastion[0].name
}

# Scoped egress (NOT egress-all): this is the gate that stops a temporal-team
# member from tunneling through the bastion to e.g. RDS:5432.
resource "aws_security_group" "bastion" {
  count       = local.temporal_ui_access_enabled
  name        = "${var.name_prefix}-bastion"
  description = "SSM tunnel bastion for ${var.name_prefix}; scoped egress only."
  vpc_id      = data.aws_vpc.selected.id

  egress {
    description = "SSM endpoints (ssm, ssmmessages, ec2messages) over HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Internal ALB (Temporal UI) within the VPC"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.selected.cidr_block]
  }

  egress {
    description = "VPC DNS resolver to resolve the internal ALB hostname"
    from_port   = 53
    to_port     = 53
    protocol    = "udp"
    cidr_blocks = [data.aws_vpc.selected.cidr_block]
  }

  egress {
    description = "VPC DNS resolver (TCP fallback)"
    from_port   = 53
    to_port     = 53
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.selected.cidr_block]
  }
}

data "aws_ssm_parameter" "al2023" {
  count = local.temporal_ui_access_enabled
  name  = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64"
}

resource "aws_instance" "bastion" {
  count                       = local.temporal_ui_access_enabled
  ami                         = data.aws_ssm_parameter.al2023[0].value
  instance_type               = var.bastion_instance_type
  subnet_id                   = local.private_subnet_ids[0]
  vpc_security_group_ids      = [aws_security_group.bastion[0].id]
  iam_instance_profile        = aws_iam_instance_profile.bastion[0].name
  associate_public_ip_address = var.allow_public_subnets_for_demo

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  tags = {
    Name = "${var.name_prefix}-bastion"
  }
}

# SSM tunnel permissions for the team role.
data "aws_iam_policy_document" "ssm_tunnel" {
  count = local.temporal_ui_access_enabled

  statement {
    sid     = "StartPortForwardSession"
    effect  = "Allow"
    actions = ["ssm:StartSession"]
    resources = [
      aws_instance.bastion[0].arn,
      "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:document/AWS-StartPortForwardingSessionToRemoteHost",
    ]

    condition {
      test     = "BoolIfExists"
      variable = "ssm:SessionDocumentAccessCheck"
      values   = ["true"]
    }
  }

  # ssmmessages:OpenDataChannel does not support resource-level scoping (it is
  # granted on "*", same as AmazonSSMManagedInstanceCore does instance-side). The
  # real boundary is StartSession above (bastion + port-forward document only)
  # plus the bastion's scoped egress.
  statement {
    sid       = "OpenDataChannel"
    effect    = "Allow"
    actions   = ["ssmmessages:OpenDataChannel"]
    resources = ["*"]
  }

  # Scoped to the session resource type (not per-owner): assumed-role sessions are
  # named "<role-session-name>-<random>", which no IAM policy variable cleanly
  # matches (${aws:userid} carries a colon).
  statement {
    sid    = "ManageSessions"
    effect = "Allow"
    actions = [
      "ssm:TerminateSession",
      "ssm:ResumeSession",
    ]
    resources = ["arn:aws:ssm:*:*:session/*"]
  }

  statement {
    sid    = "DescribeForTunnel"
    effect = "Allow"
    actions = [
      "ssm:DescribeInstanceInformation",
      "ssm:GetConnectionStatus",
      "ec2:DescribeInstances",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "ssm_tunnel" {
  count  = local.temporal_ui_access_enabled
  name   = "${var.name_prefix}-ssm-tunnel"
  policy = data.aws_iam_policy_document.ssm_tunnel[0].json
}

resource "aws_iam_role_policy_attachment" "team_ssm_tunnel" {
  count      = local.temporal_ui_access_enabled
  role       = aws_iam_role.team[0].name
  policy_arn = aws_iam_policy.ssm_tunnel[0].arn
}
