# Temporal UI access (EKS demo)

The Temporal web UI runs on the EKS demo cluster but is never exposed to the public
internet. Access is gated by three layers:

1. **Internal ALB** — the `temporal-web` service sits behind an internal-scheme ALB
   (no public IP), reachable only from inside the VPC.
2. **SSM bastion** — the only network path into the VPC. A tiny EC2 instance with no
   inbound rules and scoped egress, reachable only through AWS Systems Manager.
3. **AWS IAM** — you must be able to assume the shared `temporal-team` role and hold
   `ssm:StartSession` on the bastion. That same role is the EKS access-entry principal,
   so assuming it also grants cluster-admin `kubectl`.

```
laptop (IAM creds)
  │  assume temporal-team  →  aws ssm start-session (port forward)
  ▼
SSM bastion (no public ingress, egress: 443→SSM, 80+53→VPC only)
  │  localhost:8233  →  <internal-ALB>:80
  ▼
internal ALB (EKS Auto Mode, scheme=internal)
  ▼
temporal-web:8080
```

## One-time setup (operator)

Set the team's IAM principals and apply:

```hcl
# infra/terraform/envs/demo/terraform.tfvars
team_principal_arns = ["arn:aws:iam::<account-id>:user/alice", ...]
```

```bash
scripts/eks-demo-up.sh
```

This creates the `<name_prefix>-team` role, the SSM bastion, the internal ALB, and the
EKS access entry. The ALB Ingress is applied by the script (not Terraform) because EKS
Auto Mode configures ALB scheme/subnets through the `IngressClassParams` CRD.

## Opening the UI (team member)

```bash
ASSUME_TEAM_ROLE=1 scripts/temporal-ui.sh
# wait for "Waiting for connections...", then open:
open http://localhost:8233
```

Override the local port with `LOCAL_PORT=9233 scripts/temporal-ui.sh`. If you already
run as the team role (or have mapped your own principal), drop `ASSUME_TEAM_ROLE=1`.

Prerequisites on the laptop: the AWS CLI, the
[Session Manager plugin](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html),
and `kubectl`.

## Security model

- The Temporal UI has **no application-level auth**. Every gate is infrastructure: the
  ALB is internal, the only path in is the SSM bastion, and the bastion is IAM-gated.
- The bastion's egress is restricted to `443→SSM`, `80→VPC` (the ALB), and `53→VPC`
  (DNS). It deliberately **cannot** reach RDS (`5432`) or anything else, so the
  port-forward document can't be repurposed to tunnel to other VPC resources.
- `ssm:StartSession` is scoped to this bastion and the port-forward document, with
  `ssm:SessionDocumentAccessCheck` enforced.

To also pin the tunnel *destination* (so it can only ever reach the Temporal ALB), add
a Route53 private record for the ALB and a custom SSM document with the host/port fixed,
then scope `StartSession` to that document. Left out of the baseline because the team is
already cluster-admin and the egress scoping covers the main risk.
