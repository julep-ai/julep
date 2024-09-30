# Agent Endpoints

This document provides a reference for all Agent API endpoints in Julep.

## List Agents

- **Endpoint**: `GET /agents`
- **Description**: Retrieves a paginated list of agents.
- **Query Parameters**:
  - `limit` (optional): Number of agents to return per page.
  - `offset` (optional): Number of agents to skip.

## Create a New Agent

- **Endpoint**: `POST /agents`
- **Description**: Creates a new agent.
- **Request Body**:
  ```json
  {
    "name": "string",
    "about": "string",
    "model": "string",
    "instructions": ["string"]
  }
  ```

## Get an Agent

- **Endpoint**: `GET /agents/{id}`
- **Description**: Retrieves details of a specific agent.

## Update an Agent

- **Endpoint**: `PUT /agents/{id}`
- **Description**: Updates an existing agent (overwrites existing values).
- **Request Body**: Same as Create a New Agent

## Partially Update an Agent

- **Endpoint**: `PATCH /agents/{id}`
- **Description**: Updates an existing agent (merges with existing values).
- **Request Body**: Partial agent object

## Delete an Agent

- **Endpoint**: `DELETE /agents/{id}`
- **Description**: Deletes a specific agent.

## Get Agent Documents

- **Endpoint**: `GET /agents/{id}/docs`
- **Description**: Retrieves documents associated with an agent.

## Search Agent Documents

- **Endpoint**: `GET /agents/{id}/search`
- **Description**: Searches documents owned by an agent.

## Get Agent Tools

- **Endpoint**: `GET /agents/{id}/tools`
- **Description**: Retrieves tools associated with an agent.

## Get Agent Tasks

- **Endpoint**: `GET /agents/{id}/tasks`
- **Description**: Retrieves tasks associated with an agent.

## Create or Update Agent Tasks

- **Endpoint**: `PUT /agents/{parent_id}/tasks`
- **Description**: Creates or updates tasks for an agent.

For all endpoints, replace `{id}` or `{parent_id}` with the actual agent ID.