from prometheus_client import Counter

total_tokens_per_user = Counter(
    "total_tokens_per_user",
    "Total token count per user",
    labelnames=("developer_id",),
)
