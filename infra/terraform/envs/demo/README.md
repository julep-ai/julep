# Julep EKS Temporal Demo

This Terraform environment creates a reproducible AWS-backed version of the
`tooling/k3d-llm-demo` flow:

- EKS Auto Mode cluster with built-in `general-purpose` and `system` node pools.
- ECR repository for the demo worker image.
- RDS PostgreSQL for Temporal default and visibility persistence.
- KEDA installed through Helm.
- Temporal installed through Helm and configured against RDS.
- Demo worker Deployment plus KEDA Temporal `ScaledObject`.

Secrets are intentionally kept out of Terraform state. The Anthropic API key is
loaded from the repo `.env` file by `scripts/eks-demo-run.sh` and written as a
Kubernetes Secret immediately before the demo run.

## Usage

From the repository root:

```bash
scripts/eks-demo-up.sh
scripts/eks-demo-run.sh
scripts/eks-demo-down.sh
```

`eks-demo-up.sh` runs Terraform, updates kubeconfig, and builds/pushes the demo
worker image to the Terraform-created ECR repository.

`eks-demo-run.sh` port-forwards the Temporal frontend, starts a durable workflow,
and waits for the EKS worker pod to complete real Anthropic-backed tool use.

`eks-demo-down.sh` destroys the Terraform stack.

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

## Notes

- RDS is private to the default VPC CIDR for this demo. For production, tighten
  this to the exact node/pod security group path and use private subnets.
- Temporal's Helm chart requires an external persistence store; it does not
  install PostgreSQL itself.
- The worker image build context excludes `.env`, `.git`, `.venv`, and common
  local caches before Docker build.
