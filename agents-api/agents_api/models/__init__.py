"""
The `models` module of the agents API is designed to encapsulate all data interactions with the CozoDB database. It provides a structured way to perform CRUD (Create, Read, Update, Delete) operations and other specific data manipulations across various entities such as agents, documents, entries, sessions, tools, and users.

Each sub-module within this module corresponds to a specific entity and contains functions and classes that implement datalog queries for interacting with the database. These interactions include creating new records, updating existing ones, retrieving data for specific conditions, and deleting records. The operations are crucial for the functionality of the agents API, enabling it to manage and process data effectively for each entity.

This module also integrates with the `common` module for exception handling and utility functions, ensuring robust error management and providing reusable components for data processing and query construction.
"""
