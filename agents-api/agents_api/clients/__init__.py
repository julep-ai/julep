"""
The `clients` module contains client classes and functions for interacting with various external services and APIs, abstracting the complexity of HTTP requests and API interactions to provide a simplified interface for the rest of the application.

- `pg.py`: Handles communication with the PostgreSQL service, facilitating operations such as retrieving product information.
- `temporal.py`: Provides functionality for connecting to Temporal workflows, enabling asynchronous task execution and management.
- `feature_flags.py`: Provides feature flag management through Unleash integration for controlled feature rollouts.
"""

from .feature_flags import FeatureFlagClient, get_feature_flag_client

__all__ = ["FeatureFlagClient", "get_feature_flag_client"]
