"""
Feature flags client for Julep agents-api.
Provides OpenFeature integration with a custom Unleash provider for vendor independence.
"""

import logging
import threading
from typing import TypedDict

from openfeature import api
from openfeature.evaluation_context import EvaluationContext
from openfeature.flag_evaluation import FlagResolutionDetails, Reason
from openfeature.provider import AbstractProvider, Metadata

from agents_api.env import unleash_api_token, unleash_app_name, unleash_url

logger = logging.getLogger(__name__)


class FeatureFlagContext(TypedDict, total=False):
    """Type definition for feature flag context."""

    developer_id: str
    environment: str


class UnleashProvider(AbstractProvider):
    """OpenFeature provider for Unleash - maintains vendor independence."""

    def __init__(self):
        self._unleash_client = None
        self._initialized = False

    def get_metadata(self) -> Metadata:
        """Return provider metadata."""
        return Metadata(name="unleash-provider")

    def _ensure_initialized(self):
        """Ensure the Unleash client is initialized."""
        if not self._initialized:
            self._initialize_unleash()
            self._initialized = True

    def _initialize_unleash(self):
        """Initialize the underlying Unleash client."""
        try:
            from UnleashClient import UnleashClient

            # Prepare custom headers for authentication
            custom_headers = {}
            if unleash_api_token:
                # Unleash expects the token without "Bearer" prefix in custom headers
                custom_headers["Authorization"] = unleash_api_token

            self._unleash_client = UnleashClient(
                url=unleash_url, app_name=unleash_app_name, custom_headers=custom_headers
            )

            # Initialize the client
            self._unleash_client.initialize_client()

            logger.info(f"✅ Initialized Unleash client with URL: {unleash_url}")

        except ImportError:
            logger.warning(
                "⚠️ UnleashClient not available, feature flags will use default values"
            )
            self._unleash_client = None
        except Exception as e:
            logger.error(f"❌ Failed to initialize Unleash client: {e}")
            logger.warning("⚠️ Feature flags will use default values")
            self._unleash_client = None

    def _build_unleash_context(self, evaluation_context: EvaluationContext | None) -> dict:
        """Convert OpenFeature evaluation context to Unleash context."""
        if not evaluation_context:
            return {}

        unleash_context = {}

        # Map targeting key to userId
        if evaluation_context.targeting_key:
            # Convert UUID to string if necessary
            targeting_key = evaluation_context.targeting_key
            if hasattr(targeting_key, "__str__"):
                targeting_key = str(targeting_key)
            unleash_context["userId"] = targeting_key

        # Add all attributes, converting UUIDs to strings
        if evaluation_context.attributes:
            for key, value in evaluation_context.attributes.items():
                # Convert UUID objects to strings for JSON serialization
                if hasattr(value, "__str__") and hasattr(value, "hex"):  # UUID-like object
                    unleash_context[key] = str(value)
                else:
                    unleash_context[key] = value

        return unleash_context

    def resolve_boolean_details(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[bool]:
        """Resolve a boolean feature flag."""
        self._ensure_initialized()

        if not self._unleash_client:
            return FlagResolutionDetails(
                value=default_value,
                reason=Reason.ERROR,
                error_message="Unleash client not available",
            )

        try:
            unleash_context = self._build_unleash_context(evaluation_context)
            result = self._unleash_client.is_enabled(flag_key, unleash_context)

            logger.debug(f"Feature flag '{flag_key}' evaluated to: {result}")

            return FlagResolutionDetails(
                value=result, reason=Reason.TARGETING_MATCH if result else Reason.DEFAULT
            )

        except Exception as e:
            logger.error(f"❌ Error evaluating feature flag '{flag_key}': {e}")
            return FlagResolutionDetails(
                value=default_value, reason=Reason.ERROR, error_message=str(e)
            )

    def resolve_string_details(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[str]:
        """Resolve a string feature flag."""
        self._ensure_initialized()

        if not self._unleash_client:
            return FlagResolutionDetails(
                value=default_value,
                reason=Reason.ERROR,
                error_message="Unleash client not available",
            )

        try:
            self._build_unleash_context(evaluation_context)
            # Unleash primarily supports boolean flags, so we return default for string flags
            # In a real implementation, you might use variants or custom logic
            logger.debug(
                f"String feature flag '{flag_key}' returning default value: {default_value}"
            )

            return FlagResolutionDetails(value=default_value, reason=Reason.DEFAULT)

        except Exception as e:
            logger.error(f"❌ Error evaluating string feature flag '{flag_key}': {e}")
            return FlagResolutionDetails(
                value=default_value, reason=Reason.ERROR, error_message=str(e)
            )

    def resolve_integer_details(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[int]:
        """Resolve an integer feature flag."""
        self._ensure_initialized()

        if not self._unleash_client:
            return FlagResolutionDetails(
                value=default_value,
                reason=Reason.ERROR,
                error_message="Unleash client not available",
            )

        try:
            self._build_unleash_context(evaluation_context)
            # Unleash primarily supports boolean flags, so we return default for integer flags
            # In a real implementation, you might use variants or custom logic
            logger.debug(
                f"Integer feature flag '{flag_key}' returning default value: {default_value}"
            )

            return FlagResolutionDetails(value=default_value, reason=Reason.DEFAULT)

        except Exception as e:
            logger.error(f"❌ Error evaluating integer feature flag '{flag_key}': {e}")
            return FlagResolutionDetails(
                value=default_value, reason=Reason.ERROR, error_message=str(e)
            )

    def resolve_float_details(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[float]:
        """Resolve a float feature flag."""
        self._ensure_initialized()

        if not self._unleash_client:
            return FlagResolutionDetails(
                value=default_value,
                reason=Reason.ERROR,
                error_message="Unleash client not available",
            )

        try:
            self._build_unleash_context(evaluation_context)
            # Unleash primarily supports boolean flags, so we return default for float flags
            # In a real implementation, you might use variants or custom logic
            logger.debug(
                f"Float feature flag '{flag_key}' returning default value: {default_value}"
            )

            return FlagResolutionDetails(value=default_value, reason=Reason.DEFAULT)

        except Exception as e:
            logger.error(f"❌ Error evaluating float feature flag '{flag_key}': {e}")
            return FlagResolutionDetails(
                value=default_value, reason=Reason.ERROR, error_message=str(e)
            )

    def resolve_object_details(
        self,
        flag_key: str,
        default_value: dict | list,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[dict | list]:
        """Resolve an object feature flag."""
        self._ensure_initialized()

        if not self._unleash_client:
            return FlagResolutionDetails(
                value=default_value,
                reason=Reason.ERROR,
                error_message="Unleash client not available",
            )

        try:
            self._build_unleash_context(evaluation_context)
            # Unleash primarily supports boolean flags, so we return default for object flags
            # In a real implementation, you might use variants or custom logic
            logger.debug(
                f"Object feature flag '{flag_key}' returning default value: {default_value}"
            )

            return FlagResolutionDetails(value=default_value, reason=Reason.DEFAULT)

        except Exception as e:
            logger.error(f"❌ Error evaluating object feature flag '{flag_key}': {e}")
            return FlagResolutionDetails(
                value=default_value, reason=Reason.ERROR, error_message=str(e)
            )


class FeatureFlagClient:
    """Feature flag client wrapper for OpenFeature with Unleash provider."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_client_initialized"):
            self._client = None
            self._provider_initialized = False
            self._client_initialized = True

    def _ensure_initialized(self):
        """Ensure the OpenFeature client is initialized."""
        if not self._provider_initialized:
            self._initialize_provider()
            self._client = api.get_client("agents-api")
            self._provider_initialized = True

    def _initialize_provider(self):
        """Initialize the OpenFeature provider."""
        try:
            provider = UnleashProvider()
            api.set_provider(provider)

            logger.info("✅ Initialized OpenFeature with Unleash provider")

        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenFeature provider: {e}")
            logger.warning("⚠️ Falling back to no-op provider")
            from openfeature.provider.no_op_provider import NoOpProvider

            api.set_provider(NoOpProvider())

    def is_enabled(
        self,
        flag_name: str,
        default_value: bool | None = None,
        context: FeatureFlagContext | None = None,
    ) -> bool:
        """
        Check if a feature flag is enabled.

        Args:
            flag_name: Name of the feature flag
            default_value: Default value if flag evaluation fails (uses DEFAULT_FLAGS if None)
            context: Evaluation context (developer_id, environment, etc.)

        Returns:
            Boolean indicating if the feature is enabled
        """

        self._ensure_initialized()

        try:
            evaluation_context = None
            if context:
                evaluation_context = EvaluationContext(
                    targeting_key=context.get("developer_id"), attributes=context
                )

            result = self._client.get_boolean_value(
                flag_key=flag_name,
                default_value=default_value,
                evaluation_context=evaluation_context,
            )

            logger.debug(f"Feature flag '{flag_name}' evaluated to: {result}")
            return result

        except Exception as e:
            logger.error(f"❌ Error evaluating feature flag '{flag_name}': {e}")
            return default_value


# Global feature flag client instance
def get_feature_flag_client() -> FeatureFlagClient:
    """Get the global feature flag client instance."""
    return FeatureFlagClient()
