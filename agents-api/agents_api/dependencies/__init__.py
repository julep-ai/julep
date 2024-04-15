"""This module contains dependencies that are crucial for the operation of the agents-api. It includes components for:

- `auth.py` for API key authentication: This component is responsible for validating the API key provided in the request headers, ensuring that only authorized requests are processed.
- `developer_id.py` for developer identification: Handles developer-specific headers like `X-Developer-Id` and `X-Developer-Email`, facilitating the identification of the developer making the request.
- `exceptions.py` for custom exception handling: Defines custom exceptions that are used throughout the dependencies module to handle errors related to API security and developer identification.

These components collectively ensure the security and proper operation of the agents-api by authenticating requests, identifying developers, and handling errors in a standardized manner."""
