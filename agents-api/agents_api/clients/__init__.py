"""
The `clients` module contains client classes and functions for interacting with various external services and APIs, abstracting the complexity of HTTP requests and API interactions to provide a simplified interface for the rest of the application.

- `cozo.py`: Handles communication with the Cozo service, facilitating operations such as retrieving product information.
- `embed.py`: Manages requests to an Embedding Service for text embedding functionalities.
- `openai.py`: Facilitates interaction with OpenAI's API for natural language processing tasks.
- `temporal.py`: Provides functionality for connecting to Temporal workflows, enabling asynchronous task execution and management.
- `worker/__init__.py` and related files: Describe the role of the worker service client in sending tasks to be processed by an external worker service, focusing on memory management and other computational tasks.
"""
