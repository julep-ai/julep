# Doc Endpoints

*****
> ### This docs site is currently under construction although this github README below should suffice for now.

![](https://i.giphy.com/vR1dPIYzQmkRzLZk2w.webp)
*****


This document provides a reference for all Doc API endpoints in Julep.

## List Docs for a User

- **Endpoint**: `GET /users/{id}/docs`
- **Description**: Retrieves a paginated list of documents for a specific user.
- **Query Parameters**:
  - `limit` (optional): Number of documents to return per page.
  - `offset` (optional): Number of documents to skip.

## Create a New Doc for a User

- **Endpoint**: `POST /users/{id}/docs`
- **Description**: Creates a new document for a specific user.
- **Request Body**:
  ```json
  {
    "title": "string",
    "content": "string"
  }
  ```

## Delete a Doc for a User

- **Endpoint**: `DELETE /users/{id}/docs/{child_id}`
- **Description**: Deletes a specific document for a user.

## List Docs for an Agent

- **Endpoint**: `GET /agents/{id}/docs`
- **Description**: Retrieves a paginated list of documents for a specific agent.
- **Query Parameters**:
  - `limit` (optional): Number of documents to return per page.
  - `offset` (optional): Number of documents to skip.