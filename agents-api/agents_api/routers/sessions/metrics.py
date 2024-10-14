from prometheus_client import Counter

total_tokens_per_user = Counter(
    "total_tokens_per_user",
    "Total token count per user",
    labels=("developer_id",),
)
