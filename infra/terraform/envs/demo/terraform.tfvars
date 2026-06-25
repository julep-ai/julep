# Team principals allowed to assume the temporal-team role (Temporal UI + cluster-admin).
# Replace with your AWS account ID and the IAM users on your team.
team_principal_arns = [
  "arn:aws:iam::123456789012:user/your-iam-user",
]

# RDS auto-upgraded its minor version; pin to the live version so apply doesn't
# attempt an impossible 16.13 -> 16.6 downgrade (pre-existing drift, unrelated to UI access).
db_engine_version = "16.13"
