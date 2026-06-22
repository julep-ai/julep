# Team principals allowed to assume the temporal-team role (Temporal UI + cluster-admin).
# "All IAM users" in account 569360421603 (only `hamada` exists today).
team_principal_arns = [
  "arn:aws:iam::569360421603:user/hamada",
]

# RDS auto-upgraded its minor version; pin to the live version so apply doesn't
# attempt an impossible 16.13 -> 16.6 downgrade (pre-existing drift, unrelated to UI access).
db_engine_version = "16.13"
