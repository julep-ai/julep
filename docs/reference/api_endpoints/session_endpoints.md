# Session Endpoints

*****
> ### This docs site is currently under construction although this github README below should suffice for now.

![](https://i.giphy.com/vR1dPIYzQmkRzLZk2w.webp)
*****


This document provides a reference for all Session API endpoints in Julep.

## List Sessions

- **Endpoint**: `GET /sessions`
- **Description**: Retrieves a paginated list of sessions.
- **Query Parameters**:
  - `limit` (optional): Number of sessions to return per page.
  - `offset` (optional): Number of sessions to skip.

## Create a New Session

- **Endpoint**: `POST /sessions`
- **Description**: Creates a new session.
- **Request Body**:
  ```json
  {
    "agent_id": "string",
    "user_id": "string",
    "situation": "string",
    "token_budget": 4000,
    "context_overflow": "truncate"
  }
  ```

## Get a Session

- **Endpoint**: `GET /sessions/{id}`
- **Description**: Retrieves details of a specific session.

## Update a Session

- **Endpoint**: `PUT /sessions/{id}`
- **Description**: Updates an existing session.
- **Request Body**: Partial session object

## Delete a Session

- **Endpoint**: `DELETE /sessions/{id}`
- **Description**: Deletes a specific session.

## Get Session Messages

- **Endpoint**: `GET /sessions/{id}/messages`
- **Description**: Retrieves messages in a session.

## Create a New Message in a Session

- **Endpoint**: `POST /sessions/{id}/messages`
- **Description**: Adds a new message to a session.
- **Request Body**:
  ```json
  {
    "role": "user",
    "content": "string"
  }
  ```

## Get Session Tools

- **Endpoint**: `GET /sessions/{id}/tools`
- **Description**: Retrieves tools available in a session.

## Chat in a Session

- **Endpoint**: `POST /sessions/{id}/chat`
- **Description**: Initiates a chat interaction in a session.
- **Request Body**:
  ```json
  {
    "messages": [
      {
        "role": "user",
        "content": "string"
      }
    ],
    "stream": false,
    "max_tokens": 150
  }
  ```

For all endpoints, replace `{id}` with the actual session ID.