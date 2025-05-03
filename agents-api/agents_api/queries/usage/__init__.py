"""
The `usage` module within the `queries` package provides functionality for tracking token usage
and costs associated with LLM API calls. This includes:

- Recording prompt and completion tokens
- Calculating costs based on model pricing
- Storing usage data with developer attribution
- Supporting both standard and custom API usage

Each function in this module constructs and executes SQL queries for database operations
related to usage tracking and reporting.
"""

# ruff: noqa: F401, F403, F405

from .create_usage_record import create_usage_record
from .get_user_cost import get_user_cost

__all__ = [
    "create_usage_record",
    "get_user_cost",
]
