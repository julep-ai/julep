# Tool Endpoints

*****
> ### This docs site is currently under construction although this github README below should suffice for now.

![](https://i.giphy.com/vR1dPIYzQmkRzLZk2w.webp)
*****


This document provides a reference for all Tool API endpoints in Julep.

## List Tools for an Agent

- **Endpoint**: `GET /agents/{id}/tools`
- **Description**: Retrieves a paginated list of tools for a specific agent.
- **Query Parameters**:
  - `limit` (optional): Number of tools to return per page.
  - `offset` (optional): Number of tools to skip.

## Create a New Tool for an Agent

- **Endpoint**: `POST /agents/{id}/tools`
- **Description**: Creates a new tool for a specific agent.
- **Request Body**:
  ```json
  {
    "name": "string",
    "type": "function",
    "function": {
      "description": "string",
      "parameters": {
        "type": "object",
        "properties": {
          "param_name": {
            "type": "string",
            "description": "string"
          }
        },
        "required": ["param_name"]
      }
    }
  }
  ```

## Update a Tool for an Agent

- **Endpoint**: `PUT /agents/{id}/tools/{child_id}`
- **Description**: Updates an existing tool for a specific agent (overwrites existing values).
- **Request Body**: Same as Create a New Tool

## Partially Update a Tool for an Agent

- **Endpoint**: `PATCH /agents/{id}/tools/{child_id}`
- **Description**: Updates an existing tool for a specific agent (merges with existing values).
- **Request Body**: Partial tool object

## Delete a Tool for an Agent

- **Endpoint**: `DELETE /agents/{id}/tools/{child_id}`
- **Description**: Deletes a specific tool for an agent.

For all endpoints, replace `{id}` with the actual agent ID and `{child_id}` with the actual tool ID.