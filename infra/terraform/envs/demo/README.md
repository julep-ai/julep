# Julep EKS Temporal Application Platform

This Terraform environment creates a reproducible AWS-backed version of the
`tooling/k3d-llm-demo` flow:

- EKS Auto Mode cluster in an explicitly supplied VPC and private subnets, with
  built-in `general-purpose` and `system` node pools.
- ECR repository for immutable worker images.
- KMS-encrypted S3 CAS for application bundles and release manifests.
- Dedicated KMS-encrypted RDS PostgreSQL for Temporal default and visibility
  persistence, with 14-day backups by default.
- KEDA installed through Helm.
- A priority-class-scoped worker quota that caps the sum of model-worker pods
  across overlapping immutable releases at four by default.
- Temporal installed through Helm, configured against RDS, with 14-day workflow
  history retention by default.
- A Secrets Manager-backed AES-256-GCM payload keyring. Terraform reads the
  managed current version and materializes it into the worker namespace on
  apply.
- Private EKS API access and private subnet enforcement by default. Production
  subnets must span at least two Availability Zones, must not auto-assign public
  IPs, and must not route directly to an internet gateway.

Terraform owns the cluster and shared services. `julep apply` publishes an
immutable release and reconciles one `infra/helm/julep-worker` release per
logical lane and immutable release. Each release polls its own derived task
queue, so applying capacity does not move existing workflows or new traffic.
Every model worker is pinned to one concurrent activity and the shared worker
quota bounds all coexisting releases together, preserving the global model
concurrency ceiling during drain and rollback.
Terraform does not install a worker by default
(`deploy_demo_worker = false`).

Generated database and payload-codec secrets are sensitive values in Terraform
state, so the state backend must be encrypted and access-controlled. They are
never checked into source. The Anthropic API key is not managed by Terraform: it
is loaded from the repo `.env` file by `scripts/eks-demo-run.sh` and written as a
Kubernetes Secret immediately before the demo run.

## Usage

From the repository root:

```bash
scripts/eks-demo-up.sh
scripts/eks-demo-run.sh
scripts/eks-demo-down.sh
```

`eks-demo-up.sh` supplies disposable-demo overrides, runs Terraform, updates
kubeconfig, and builds/pushes the demo worker image to the Terraform-created ECR
repository. To preserve the workstation demo, the wrapper discovers the
account's default VPC/subnets and explicitly enables public subnet and EKS API
access. Set `DEMO_AWS_REGION`, `DEMO_VPC_ID`, and
`DEMO_SUBNET_IDS_JSON='["subnet-...","subnet-..."]'` to override discovery.
`DEMO_EXCLUDED_AZS` is a comma-separated list and defaults to `us-east-1e` for
compatibility with the original demo. Production automation should invoke
Terraform directly from private network access and leave the secure defaults
unchanged.
The wrappers set the Secrets Manager recovery window to zero so a destroy and
recreate can immediately reuse the demo secret names, and explicitly set
`rds_skip_final_snapshot = true` so disposable database teardown remains fast.
Production keeps 30 days and retains a final RDS snapshot by default.

`eks-demo-run.sh` port-forwards the Temporal frontend, starts a durable workflow,
and waits for the EKS worker pod to complete real Anthropic-backed tool use.

`eks-demo-down.sh` destroys the Terraform stack.

## Production network inputs

The stack never discovers a production network. Supply an existing VPC and at
least two private subnets in distinct Availability Zones:

```hcl
vpc_id = "vpc-0123456789abcdef0"
private_subnet_ids = [
  "subnet-0123456789abcdef0",
  "subnet-0fedcba9876543210",
]
```

`name_prefix` is shared by AWS, Kubernetes, RDS, and the release CAS bucket. It
must be 1-41 lowercase characters, start with a letter, use only letters,
digits, or single hyphens, and not end with a hyphen. The 41-character ceiling
reserves room for `-releases-<12-digit-account-id>` within S3's 63-character
bucket-name limit.

The private subnets need NAT egress or the appropriate VPC endpoints for ECR,
S3, STS, SSM, Secrets Manager, and any external model providers. Terraform and
Helm must run from a host that can reach the private EKS endpoint. The
`allow_public_subnets_for_demo` input is a fail-loud disposable-demo escape
hatch and must remain `false` in production.

## RDS deletion policy

Deletion protection and final-snapshot retention are independent controls.
Production defaults to both `rds_deletion_protection = true` and
`rds_skip_final_snapshot = false`. To intentionally tear down production, first
apply with deletion protection disabled while leaving final-snapshot retention
enabled, then destroy:

```hcl
rds_deletion_protection = false
rds_skip_final_snapshot = false
```

The retained snapshot is named
`<name_prefix>-final-<persisted-random-suffix>`. The suffix is stable for one
stack and regenerated after a full destroy/recreate, so an older retained
snapshot cannot make a later teardown fail from an identifier collision.
Terraform rejects the unsafe pre-armed combination of deletion protection on
and final-snapshot skipping on. Only the disposable demo wrappers set both
`rds_deletion_protection = false` and `rds_skip_final_snapshot = true`.

## Temporal UI access

The Temporal web UI is reachable without any public endpoint. `eks-demo-up.sh`
provisions an internal-scheme ALB in front of the `temporal-web` service, and the
team reaches it by tunneling through an SSM-managed bastion.

1. Set the team's IAM principals so the access stack is created:

   ```hcl
   # terraform.tfvars
   team_principal_arns = [
     "arn:aws:iam::<account-id>:user/alice",
     "arn:aws:iam::<account-id>:role/SomeSSORole",
   ]
   ```

   Leaving `team_principal_arns` empty disables the whole access stack (no bastion,
   no role). `temporal_ui_enabled = false` turns it off entirely.

2. Apply (`scripts/eks-demo-up.sh`). This creates the `<name_prefix>-team` role
   (cluster-admin via an EKS access entry), the SSM bastion, and the internal ALB.

3. From a laptop with creds that can assume the team role:

   ```bash
   ASSUME_TEAM_ROLE=1 scripts/temporal-ui.sh
   # then open http://localhost:8233
   ```

See `docs/temporal-ui-access.md` for the full flow and security model.

## Application releases

Configure an explicit application and environment; no AST discovery is used:

```toml
[tool.julep]
application = "memory_app:application"

[tool.julep.env.production]
temporal_address = "temporal-frontend.temporal.svc.cluster.local:7233"
release_store = "s3://<release-bucket>/julep"
worker_image = "<ecr-repository>@sha256:<image-digest>"
helm_chart = "infra/helm/julep-worker"
kubernetes_namespace = "julep-demo"
worker_context_factory = "mcp_memory_server.julep_flows.episode_summary_worker:build_summary_worker_context"
worker_service_account = "julep-worker"
worker_priority_class = "julep-model-worker"
payload_encryption_secret = "temporal-payload-codec"

[tool.julep.env.production.queues]
summary = "memory-summary"
```

The demo Terraform stack provisions both named resources. On another cluster,
omit `worker_priority_class` unless that cluster provides it, and set
`payload_encryption_secret` to an existing Secret in `kubernetes_namespace`
containing `keyring` and `active-key-id` entries.

Then run `julep plan --env production`, `julep apply --env production`, and
`julep status --env production`. Apply publishes/reconciles capacity only; it
never changes an application's traffic route. The apply output records the
release-specific task queue that the router must select during cutover; the
previous lane release and queue remain available for drain/rollback.

Install `julep[store,temporal]` (plus application-specific extras) and provide
authenticated `helm`, `kubectl`, and `temporal` CLIs on the control-plane host.
Before applying, export `JULEP_BUNDLE_SIGNING_KEY` as a 64-hex Ed25519 seed or the
path to a file containing one. Configure its 64-hex public key as the non-secret
`JULEP_BUNDLE_ALLOWED_SIGNERS` value under the environment's
`worker_environment`; a configured allow-list that omits the publishing key is
rejected. Plan and status use this public allow-list without requiring the
private key.

## Notes

- RDS is deployed into the supplied private subnets and only admits PostgreSQL
  from the EKS cluster security group.
- Temporal's Helm chart requires an external persistence store; it does not
  install PostgreSQL itself.
- Payload key rotation is additive: supply the retained key map through the
  sensitive `temporal_payload_keyring` input, apply with the new key present,
  roll every client and worker, switch `temporal_payload_active_key_id`, apply
  and roll again, and retain old keys through the maximum Temporal history
  retention window. Synchronization is apply-time, not a continuous controller.
- The worker image build context excludes `.env`, `.git`, `.venv`, and common
  local caches before Docker build.
