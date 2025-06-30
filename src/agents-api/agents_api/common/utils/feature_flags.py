"""
Feature flags utility module for Julep agents-api.
Provides convenience functions for feature flag management.
"""

from agents_api.clients.feature_flags import FeatureFlagContext, get_feature_flag_client


def get_environment() -> str:
    """Get current environment for feature flag context."""
    return "development"


def get_feature_flag_value(
    flag_name: str,
    default_value: bool = False,
    developer_id: str | None = None,
    **additional_context,
) -> bool:
    """
    Generic function to get any boolean feature flag value.

    Args:
        flag_name: Name of the feature flag
        default_value: Default value if flag evaluation fails
        developer_id: Developer ID for targeting (optional)
        **additional_context: Additional context attributes

    Returns:
        The feature flag value
    """
    context: FeatureFlagContext = {"environment": get_environment(), **additional_context}
    if developer_id:
        context["developer_id"] = developer_id

    return get_feature_flag_client().is_enabled(flag_name, default_value, context)
