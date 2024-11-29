# User Endpoints


This document provides a reference for all User API endpoints in Julep.

## List Users

- **Endpoint**: `GET /users`
- **Description**: Retrieves a paginated list of users.
- **Query Parameters**:
  - `limit` (optional): Number of users to return per page.
  - `offset` (optional): Number of users to skip.

## Create a New User

- **Endpoint**: `POST /users`
- **Description**: Creates a new user.
- **Request Body**:
  ```json
  {
    "name": "string",
    "about": "string"
  }
  ```

## Get a User

- **Endpoint**: `GET /users/{id}`
- **Description**: Retrieves details of a specific user.

## Update a User

- **Endpoint**: `PUT /users/{id}`
- **Description**: Updates an existing user (overwrites existing values).
- **Request Body**: Same as Create a New User

## Partially Update a User

- **Endpoint**: `PATCH /users/{id}`
- **Description**: Updates an existing user (merges with existing values).
- **Request Body**: Partial user object

## Delete a User

- **Endpoint**: `DELETE /users/{id}`
- **Description**: Deletes a specific user.

## Get User Documents

- **Endpoint**: `GET /users/{id}/docs`
- **Description**: Retrieves documents associated with a user.

## Search User Documents

- **Endpoint**: `GET /users/{id}/search`
- **Description**: Searches documents owned by a user.

For all endpoints, replace `{id}` with the actual user ID.