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
  worker_task_queue       = "julep"
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
  for_each    = var.temporal_ui_enabled ? toset(local.control_plane_subnet_ids) : toset([])
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
  vpc_id      = data.aws_vpc.default.id

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
    cidr_blocks = [data.aws_vpc.default.cidr_block]
  }

  egress {
    description = "VPC DNS resolver to resolve the internal ALB hostname"
    from_port   = 53
    to_port     = 53
    protocol    = "udp"
    cidr_blocks = [data.aws_vpc.default.cidr_block]
  }

  egress {
    description = "VPC DNS resolver (TCP fallback)"
    from_port   = 53
    to_port     = 53
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.default.cidr_block]
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
  subnet_id                   = local.control_plane_subnet_ids[0]
  vpc_security_group_ids      = [aws_security_group.bastion[0].id]
  iam_instance_profile        = aws_iam_instance_profile.bastion[0].name
  associate_public_ip_address = true

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
