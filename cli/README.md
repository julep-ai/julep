# Julep CLI Specification

The `julep` CLI tool provides a comprehensive command-line interface for interacting with the Julep platform. It enables authentication, management of agents, tasks, and tools, project initialization, synchronization, interaction with agents via chat, task execution, log retrieval, and more. This specification outlines the commands, options, and best practices to ensure a consistent and user-friendly experience.

## Table of Contents

- [Julep CLI Specification](#julep-cli-specification)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
    - [Components](#components)
    - [Schema for `julep.yaml`](#schema-for-julepyaml)
    - [Schema for `julep-lock.json`](#schema-for-julep-lockjson)
    - [How the lock file is used](#how-the-lock-file-is-used)
      - [Version Control](#version-control)
      - [`relationships` Details](#relationships-details)
      - [How the CLI Should Use It](#how-the-cli-should-use-it)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Commands](#commands)
    - [Authentication](#authentication)
      - [`julep auth`](#julep-auth)
    - [Agent Management](#agent-management)
      - [`julep agents`](#julep-agents)
      - [Subcommands](#subcommands)
        - [`julep agents create`](#julep-agents-create)
        - [`julep agents update`](#julep-agents-update)
        - [`julep agents delete`](#julep-agents-delete)
        - [`julep agents list`](#julep-agents-list)
        - [`julep agents get`](#julep-agents-get)
    - [Task Management](#task-management)
      - [`julep tasks`](#julep-tasks)
      - [Subcommands](#subcommands-1)
        - [`julep tasks create`](#julep-tasks-create)
        - [`julep tasks update`](#julep-tasks-update)
        - [`julep tasks delete`](#julep-tasks-delete)
        - [`julep tasks list`](#julep-tasks-list)
    - [Tool Management](#tool-management)
      - [`julep tools`](#julep-tools)
      - [Subcommands](#subcommands-2)
        - [`julep tools create`](#julep-tools-create)
        - [`julep tools update`](#julep-tools-update)
        - [`julep tools delete`](#julep-tools-delete)
        - [`julep tools list`](#julep-tools-list)
    - [Project Initialization](#project-initialization)
      - [`julep init`](#julep-init)
    - [Synchronization](#synchronization)
      - [`julep sync`](#julep-sync)
    - [Importing Agents](#importing-agents)
      - [`julep import`](#julep-import)
    - [Chat Interaction](#chat-interaction)
      - [`julep chat`](#julep-chat)
    - [Task Execution](#task-execution)
      - [`julep run`](#julep-run)
    - [Execution Management](#execution-management)
      - [`julep executions`](#julep-executions)
      - [Subcommands](#subcommands-3)
        - [`julep executions create`](#julep-executions-create)
        - [`julep executions list`](#julep-executions-list)
        - [`julep executions cancel`](#julep-executions-cancel)
    - [Log Retrieval](#log-retrieval)
      - [`julep logs`](#julep-logs)
    - [Project Assistant](#project-assistant)
      - [`julep assistant`](#julep-assistant)
    - [Common Commands](#common-commands)
      - [Version](#version)
        - [`julep --version`, `julep -v`](#julep---version-julep--v)
      - [Help](#help)
        - [`julep`, `julep --help`, `julep -h`](#julep-julep---help-julep--h)
      - [Global Options](#global-options)
        - [Standard Input/Output Handling](#standard-inputoutput-handling)
        - [Quiet Mode](#quiet-mode)
        - [Color Output](#color-output)
  - [TODO](#todo)

---

## Overview

The `julep` CLI is designed to streamline interactions with the Julep platform, allowing developers to efficiently manage AI agents, tasks, tools, and projects directly from the terminal. It adheres to industry-standard CLI conventions, ensuring an intuitive and predictable user experience.

For commands that output raw data (like `get`, `list`, etc.), the CLI will print/return YAML by default. If the `--json` flag is specified, the output will be in JSON format instead.

### Components

There are 3 main components to the `julep` CLI:

1. The project management stuff (init, sync, etc.)
2. The static stuff (agents, tasks, tools, etc.)
3. The dynamic stuff (chat, run, logs, etc.)

Different files that are important:
- `~/.config/julep/config.yml`: The configuration file for the CLI.
- `julep.yaml`: The configuration file for the project.
- `julep-lock.json`: The lock file for the project that tracks server state.
- `src/*.yaml`: The object definitions for the project (agents, tasks, tools, etc.).

### Schema for `julep.yaml`

```yaml
agents:
- definition: path/to/agent.yaml
- definition: path/to/agent.yaml

tasks:
- agent_id: "{agents[0].id}"
  definition: path/to/task.yaml
- agent_id: "{agents[1].id}"
  definition: path/to/task.yaml

tools:
- agent_id: "{agents[0].id}"
  definition: path/to/tool.yaml
- agent_id: "{agents[1].id}"
  definition: path/to/tool.yaml
```

### Schema for `julep-lock.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://example.com/julep-lock.schema.json",
  "title": "Julep Lockfile Schema",
  "type": "object",
  "properties": {
    "lockfile_version": {
      "type": "string",
      "description": "Version of the lockfile format."
    },
    "updated_at": {
      "type": "string",
      "format": "date-time",
      "description": "Timestamp representing when the lockfile was last updated."
    },
    "agents": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "description": "Path to the agent definition file."
          },
          "id": {
            "type": "string",
            "description": "Unique identifier of the agent from the remote server."
          },
          "last_synced": {
            "type": "string",
            "format": "date-time",
            "description": "Timestamp of the last synchronization with the remote server."
          },
          "revision_hash": {
            "type": "string",
            "description": "Hash of the local file used for change detection."
          }
        },
        "required": ["path", "id", "last_synced", "revision_hash"],
        "additionalProperties": false
      }
    },
    "tasks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "description": "Path to the task definition file."
          },
          "id": {
            "type": "string",
            "description": "Unique identifier of the task from the remote server."
          },
          "last_synced": {
            "type": "string",
            "format": "date-time",
            "description": "Timestamp of the last synchronization with the remote server."
          },
          "revision_hash": {
            "type": "string",
            "description": "Hash of the local file used for change detection."
          }
        },
        "required": ["path", "id", "last_synced", "revision_hash"],
        "additionalProperties": false
      }
    },
    "tools": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "description": "Path to the tool definition file."
          },
          "id": {
            "type": "string",
            "description": "Unique identifier of the tool from the remote server."
          },
          "last_synced": {
            "type": "string",
            "format": "date-time",
            "description": "Timestamp of the last synchronization with the remote server."
          },
          "revision_hash": {
            "type": "string",
            "description": "Hash of the local file used for change detection."
          }
        },
        "required": ["path", "id", "last_synced", "revision_hash"],
        "additionalProperties": false
      }
    },
    "relationships": {
      "type": "object",
      "properties": {
        "tasks": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "id": {
                "type": "string",
                "description": "Identifier of the task."
              },
              "agent_id": {
                "type": "string",
                "description": "Identifier of the associated agent."
              }
            },
            "required": ["id", "agent_id"],
            "additionalProperties": false
          }
        },
        "tools": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "tool_id": {
                "type": "string",
                "description": "Identifier of the tool."
              },
              "agent_id": {
                "type": "string",
                "description": "Identifier of the associated agent."
              }
            },
            "required": ["id", "agent_id"],
            "additionalProperties": false
          }
        }
      },
      "required": ["tasks", "tools"],
      "additionalProperties": false
    }
  },
  "required": ["lockfile_version", "agents", "tasks", "tools", "relationships"],
  "additionalProperties": false
} 
```

**Example:**

```json
{
  // Minimal versioning for the lock file's structure. 
  // Bump if you ever change this schema in a backward-incompatible way.
  "lockfile_version": "0.1.0",

  // (Optional) Timestamp or ISO string representing when this lock was last updated.
  // "updated_at": "2025-01-27T14:13:52.123Z",

  // Agents, tasks, and tools sections store local definitions alongside remote IDs.
  "agents": [
    {
      "path": "src/agents/awesome-agent.yaml",
      "id": "agent_123456",               // The remote ID from the server
      "last_synced": "2025-01-27T14:13:52.123Z",
      "revision_hash": "abc123def456..."   // Hash of local file for change detection
    }
  ],
  "tasks": [
    {
      "path": "src/tasks/generate-story.yaml",
      "id": "task_789abcd",
      "last_synced": "2025-01-27T14:13:52.125Z",
      "revision_hash": "def456abc789..."
    }
  ],
  "tools": [
    {
      "path": "src/tools/web_search.yaml",
      "id": "tool_xyz999",
      "last_synced": "2025-01-27T14:13:52.130Z",
      "revision_hash": "ghi678jkl012..."
    }
  ],

  // A separate section for relationships/"foreign key" references
  // so that tasks and tools can specify which agent they relate to.
  "relationships": {
    "tasks": [
      {
        "id": "task_789abcd",
        "agent_id": "agent_123456"
      }
    ],
    "tools": [
      {
        "id": "tool_xyz999",
        "agent_id": "agent_123456"
      }
    ]
  }
}
```

### How the lock file is used

The `julep-lock.json` file serves several critical purposes:

1. **State Tracking**: It maintains a record of the remote server state, mapping local files to their remote counterparts by storing IDs and revision hashes.

2. **Change Detection**: The `revision_hash` field enables the CLI to detect when local files have changed and need to be synced.

3. **Relationship Management**: Through the `relationships` section, it tracks which tasks and tools are associated with which agents.

4. **Team Collaboration**: By checking the lock file into version control, team members can share the same remote state and avoid conflicts.

#### Version Control

The `julep-lock.json` file **should be committed to version control**. This is important because:

- It ensures all team members are working with the same remote state
- It prevents accidental creation of duplicate remote resources
- It maintains consistent relationships between agents, tasks, and tools across the team
- It enables tracking of remote state changes through version control history

This is similar to how package managers like npm and yarn use lock files to ensure consistent dependencies across team members.

#### `relationships` Details

*   `**tasks**`: An array where each item includes `id` and `agent_id`.
    *   This is the CLI's record that _this remote task is associated with that remote agent._
*   `**tools**`: Same pattern: a `id` references a remote tool, and `agent_id` references the remote agent.
*   You could expand the `relationships` object to store other relationships (e.g., task-tool references) if that's a thing in your system. You have the flexibility to break down relationships by type.

#### How the CLI Should Use It

**On** `**julep sync**`:  
1.  Parse `julep.yaml` plus any local `.yaml` definitions.
2.  Compare to `julep-lock.json`:
      *   If you find a definition that's **not** in the lock file, create it on the server. Then save the new `id` to the lock file.
      *   If you see a definition in the lock file but the `revision_hash` changed, update it on the server.
      *   If an entry is in the lock file but the file no longer exists locally, prompt the user to delete the remote definition (or do so automatically).
3.  Do the same logic for tasks and tools.
4.  Finally, examine or rebuild the `relationships` array by reading each local definition. If a local definition says "this task uses agent X," the CLI sets or updates the corresponding relationship in the lock file.

---

## Installation

The `julep` CLI can be installed using pipx:

```bash
pipx install julep-cli
```

This will install the CLI tool which can then be invoked using the `julep` command:

```bash
julep --version
```

Note: While the package name is `julep-cli`, the installed command is simply `julep`.

---

## Configuration

The CLI stores configuration data, such as the API key, in `~/.config/julep/config.yml`. After authentication, this file is created automatically.

---

## Commands

> **Note**: This CLI is still in development and is not yet stable. Currently implemented commands include:
> - [Authentication](#authentication)
> - [Project Management](#project-management)
> - [Task Execution](#task-execution)
> - [Miscellaneous](#miscellaneous)

### Authentication

Authenticate with the Julep platform by providing your API key.

#### `julep auth`

**Description:**  
Prompt the user to enter their API key and save it to the configuration file.

**Usage:**

```bash
julep auth
```

**Behavior:**

1. Prompts the user to input their API key.
2. Saves the API key to `~/.config/julep/config.yml`.

**Options:**

- `--api-key`, `-k`: Directly provide the API key without prompting.
- `--environment`, `-e`: Set the environment to use. Defaults to `production`.

**Example:**

```bash
julep auth --api-key your_julep_api_key
```

---

### Agent Management

Manage AI agents within the Julep platform.

#### `julep agents`

**Description:**  
Parent command for managing agents. Includes subcommands to create, update, delete, and list agents.

#### Subcommands

1. **Create an Agent**

   ##### `julep agents create`

   **Description:**  
   Create a new AI agent.

   **Usage:**

   ```bash
   julep agents create --name "Agent Name" --model "Model Name" --about "Agent Description"
   ```

   **Options:**

   - `--name`, `-n` (optional): Name of the agent.
   - `--model`, `-m` (optional): Model to be used by the agent (e.g., `gpt-4`).
   - `--about`, `-a` (optional): Description of the agent.
   - `--default-settings`, (optional): Default settings for the agent. Value is parsed as json.
   - `--metadata`, (optional): Metadata for the agent. Value is parsed as json.
   - `--instructions`, (optional): Instructions for the agent, repeat the option to add multiple.
   - `--definition`, `-d` (optional): Path to an agent definition file.

   Either provide a definition file or use the other options to create the agent.

   **Example:**

   ```bash
   julep agents create --name "Storyteller" --model "gpt-4" --about "An agent that crafts engaging stories."
   ```

2. **Update an Agent**

   ##### `julep agents update`

   **Description:**  
   Update an existing AI agent's details.

   **Usage:**

   ```bash
   julep agents update --id <agent_id> [--name "New Name"] [--model "New Model"] [--about "New Description"] [--metadata '{"key": "value"}'] [--instructions "Instruction 1"] [--instructions "Instruction 2"]
   ```

   **Options:**

   - `--id`, (required): ID of the agent to update.
   - `--name`, `-n` (optional): New name for the agent.
   - `--model`, `-m` (optional): New model for the agent.
   - `--about`, `-a` (optional): New description for the agent.
   - `--metadata`, (optional): Metadata for the agent. Value is parsed as json.
   - `--default-settings`, (optional): Default settings for the agent. Value is parsed as json.
   - `--instructions`, (optional): Instructions for the agent, repeat the option to add multiple.

   **Example:**

   ```bash
   julep agents update --id abc123 --name "Creative Storyteller" --model "gpt-4.5"
   ```

3. **Delete an Agent**

   ##### `julep agents delete`

   **Description:**  
   Delete an existing AI agent.

   **Usage:**

   ```bash
   julep agents delete --id <agent_id> [--force]
   ```

   **Behavior:**

   - If `--force` is not provided, the CLI will prompt for confirmation before deleting the agent.

   **Options:**

   - `--id`, (required): ID of the agent to delete.
   - `--force`, `-f` (optional): Force the deletion without prompting for confirmation.

   **Example:**

   ```bash
   julep agents delete --id abc123
   ```

4. **List Agents**

   ##### `julep agents list`

   **Description:**  
   List all AI agents or filter based on metadata.

   **Usage:**

   ```bash
   julep agents list [--metadata-filter '{"key": "value"}'] [--json]
   ```

   **Options:**

   - `--metadata-filter`, (optional): Filter agents based on specific criteria (JSON).
   - `--json`, (optional): Output the list in JSON format.

   **Example:**

   ```bash
   julep agents list --metadata-filter '{"model": "gpt-4"}'
   ```

5. **Get an Agent**

   ##### `julep agents get`

   **Description:**  
   Get an agent by its ID.

   **Usage:**

   ```bash
   julep agents get --id <agent_id> [--json]
   ```

   **Options:**

   - `--json`, (optional): Output the agent in JSON format.

   **Example:**

   ```bash
   julep agents get --id abc123
   ```


---

### Task Management

Manage tasks associated with AI agents.

#### `julep tasks`

**Description:**  
Parent command for managing tasks. Includes subcommands to create, update, delete, and list tasks.

#### Subcommands

1. **Create a Task**

   ##### `julep tasks create`

   **Description:**  
   Create a new task for an agent.

   **Usage:**

   ```bash
   julep tasks create --name "Task Name" --agent-id <agent_id> --definition "path/to/task.yaml" [--metadata '{"status": "beta"}'] [--inherit-tools]
   ```

   **Options:**

   - `--agent-id`, `-a` (required): ID of the agent the task is associated with.
   - `--definition`, `-d` (required): Path to the task definition YAML file.
   - `--name`, `-n` (optional): Name of the task (if not provided, the name will be the file name of the definition).
   - `--description`, (optional): Description of the task (if not provided, the description will be the file name of the definition).
   - `--metadata`, (optional): Metadata for the task. Value is parsed as json.
   - `--inherit-tools`, (optional): Inherit tools from the associated agent. Defaults to false if not specified.

   If passed other options, they override the values in the definition file.

   **Example:**

   ```bash
   julep tasks create --name "Generate Story" --description "Writes a short story" --agent-id abc123 --definition ./tasks/generate_story.yaml --metadata '{"category":"fiction"}'
   ```

2. **Update a Task**

   ##### `julep tasks update`

   **Description:**  
   Update an existing task's details.

   **Usage:**

   ```bash
   julep tasks update --id <task_id> [--name "New Name"] [--description "New Description"] [--definition "new/path/to/task.yaml"] [--metadata '{"status": "published"}'] [--inherit-tools true|false]
   ```

   **Options:**

   - `--id`, (required): ID of the task to update.
   - `--name`, `-n` (optional): New name for the task.
   - `--description`, (optional): New description for the task.
   - `--definition`, `-d` (optional): Path to the updated task definition YAML file.
   - `--metadata`, (optional): Metadata for the task. Value is parsed as json.
   - `--inherit-tools`, (optional): Inherit tools from the associated agent (true/false).

   **Example:**

   ```bash
   julep tasks update --id task456 --name "Advanced Story Generation" --metadata '{"priority":"high"}'
   ```

3. **Delete a Task**

   ##### `julep tasks delete`

   **Description:**  
   Delete an existing task.

   **Usage:**

   ```bash
   julep tasks delete --id <task_id> [--force]
   ```

   **Options:**

   - `--id`, (required): ID of the task to delete.
   - `--force`, `-f` (optional): Force the deletion without prompting for confirmation.

   **Example:**

   ```bash
   julep tasks delete --id task456
   ```

4. **List Tasks**

   ##### `julep tasks list`

   **Description:**  
   List all tasks or filter based on criteria.

   **Usage:**

   ```bash
   julep tasks list [--agent-id <agent_id>] [--json]
   ```

   **Options:**

   - `--agent-id`, `-a` (optional): Filter tasks by associated agent ID.
   - `--json`, (optional): Output the list in JSON format.

   **Example:**

   ```bash
   julep tasks list --agent-id abc123
   ```

---

### Tool Management

Manage tools associated with AI agents.

#### `julep tools`

**Description:**  
Parent command for managing tools. Includes subcommands to create, update, delete, and list tools.

#### Subcommands

1. **Create a Tool**

   ##### `julep tools create`

   **Description:**  
   Create a new tool for an agent.

   **Usage:**

   ```bash
   julep tools create --name "Tool Name" --type <type> --agent-id <agent_id> --definition "path/to/config.yaml"
   ```

   **Options:**

   - `--agent-id`, `-a` (required): ID of the agent the tool is associated with.
   - `--definition`, `-d` (required): Path to the tool configuration YAML file.
   - `--name`, `-n` (optional): Name of the tool.

   If passed other options, they override the values in the definition file.

   **Example:**

   ```bash
   julep tools create --name "Web Search" --agent-id abc123 --definition ./tools/web_search.yaml
   ```

2. **Update a Tool**

   ##### `julep tools update`

   **Description:**  
   Update an existing tool's details.

   **Usage:**

   ```bash
   julep tools update --id <tool_id> [--name "New Name"] [--definition "new/path/to/config.yaml"]
   ```

   **Options:**

   - `--id`, (required): ID of the tool to update.
   - `--definition`, `-d` (optional): Path to the updated tool configuration YAML file.
   - `--name`, `-n` (optional): New name for the tool.

   **Example:**

   ```bash
   julep tools update --id tool789 --name "Advanced Web Search"
   ```

3. **Delete a Tool**

   ##### `julep tools delete`

   **Description:**  
   Delete an existing tool.

   **Usage:**

   ```bash
   julep tools delete --id <tool_id> [--force]
   ```

   **Options:**

   - `--id`, (required): ID of the tool to delete.
   - `--force`, `-f` (optional): Force the deletion without prompting for confirmation.

   **Example:**

   ```bash
   julep tools delete --id tool789
   ```

4. **List Tools**

   ##### `julep tools list`

   **Description:**  
   List all tools or filter based on criteria.

   **Usage:**

   ```bash
   julep tools list [--agent-id <agent_id>] [--json]
   ```

   **Options:**

   - `--agent-id`, `-a` (optional): Filter tools by associated agent ID.
   - `--task-id`, `-t` (optional): Filter tools by associated task ID.
   - `--json`, (optional): Output the list in JSON format.

   One of `--agent-id` or `--task-id` must be provided.

   **Example:**

   ```bash
   julep tools list --agent-id abc123
   ```

---

### Project Initialization

Initialize a new Julep project using predefined templates.

#### `julep init`

**Description:**  
Initialize a new Julep project by copying a template from the library repository.

**Usage:**

```bash
julep init --template=<template_name> [--path=<path>]
```

**Options:**

- `--template`, `-t` (optional): Name of the template to use (defaults to `hello-world`).
- `--path`, `-p` (optional): Destination directory for the initialized project (default: current directory).
- `--yes`, `-y` (optional): Skip confirmation prompt.

Confirm before copying the template to the destination directory. Then open the project README.md

**Behavior:**

1. Copies the specified template folder from the `/library` repository to the destination directory.
2. Ensures the destination directory contains a `julep.yaml` file, validating it as a valid Julep package.

---

### Synchronization

Synchronize local directories with Julep packages.

#### `julep sync`

**Description:**  
Synchronize the local Julep package with the Julep platform.

**Usage:**

```bash
julep sync --source=<path> [--force-local] [--force-remote] [--watch]
```

**Options:**

- `--source`, `-s` (required): Source directory containing the Julep package (must include `julep.yaml`).
- `--force-local`, (optional): Force the local state to be overwritten by the remote state.
- `--force-remote`, (optional): Force the remote state to be overwritten by the local state.
- `--watch`, `-w` (optional): Watch the source directory for changes and synchronize automatically.

**Behavior:**

1. Validates the presence of `julep.yaml` in the source directory.
2. Compares local and remote states:
   - If local is newer and no conflicts, updates remote
   - If remote is newer and no `--force-local` specified, raises an error with guidance
   - If `--force-local` specified, updates local to match remote
   - If `--force-remote` specified, updates remote to match local
3. Provides feedback on the synchronization status.

---

### Importing Agents

Import an agent from the Julep platform.

#### `julep import`

**Description:**  
Import an agent from the Julep platform.

**Usage:**

```bash
julep import --id <agent_id> --output=<path>
```

**Options:**

- `--id`, (required): ID of the agent to import.
- `--output`, `-o` (optional): Path to the directory to save the imported agent (defaults to the current directory).
- `--yes`, `-y` (optional): Skip confirmation prompt.

---

### Chat Interaction

Interact with a specific agent via chat.

#### `julep chat`

**Description:**  
Initiate an interactive chat session with a specified AI agent.

**Usage:**

```bash
julep chat --agent=<agent_id_or_name>
```

**Options:**

- `--agent`, `-a` (required): ID or name of the agent to chat with.
- `--situation`, `-s` (optional): Situation to chat about.
- `--settings`, (optional): Chat settings (JSON string).

**Example:**

```bash
julep chat --agent "Storyteller"
```

**Behavior:**

1. Initiates an interactive terminal session.
2. Sends user inputs to the agent and displays responses in real-time.
3. Optionally loads and saves chat history based on provided options.

---

### Task Execution

Execute specific tasks with provided inputs.

#### `julep run`

**Description:**  
Run a defined task with specified input parameters.

**Usage:**

```bash
julep run --task=<task_id_or_name> --input='<input_json>'
```

**Options:**

- `--task`, `-t` (required): ID or name of the task to execute.
- `--input`, (optional): JSON string representing the input for the task (defaults to `{}`).
- `--input-file`, (optional): Path to a file containing the input for the task.
- `--wait`, (optional): Wait for the task to complete before exiting, stream logs to stdout.

**Example:**

```bash
julep run --task "Generate Story" --input '{"idea": "A cat who learns to fly"}'
```

**Behavior:**

1. Submits the task for execution with the provided input.
2. If `--wait` is specified, waits for the task to complete and outputs the final result.

---

### Execution Management

Manage task executions.

#### `julep executions`

**Description:**  
Parent command for managing executions. Includes subcommands to create, list, and cancel executions.

#### Subcommands

1. **Create an Execution**

   ##### `julep executions create`

   **Description:**  
   Create a new execution for a task.

   **Usage:**

   ```bash
   julep executions create --task=<task_id_or_name> --input='<input_json>'
   ```

   **Options:**

   - `--task`, `-t` (required): ID or name of the task to execute.
   - `--input`, (optional): JSON string representing the input for the task (defaults to `{}`).
   - `--input-file`, (optional): Path to a file containing the input for the task.

   **Example:**

   ```bash
   julep executions create --task "Generate Story" --input '{"idea": "A cat who learns to fly"}'
   ```

2. **List Executions**

   ##### `julep executions list`

   **Description:**  
   List all executions or filter based on criteria.

   **Usage:**

   ```bash
   julep executions list [--task-id <task_id>] [--json]
   ```

   **Options:**

   - `--task-id`, `-t` (optional): Filter executions by associated task ID.
   - `--json`, (optional): Output the list in JSON format.

   **Example:**

   ```bash
   julep executions list --task-id abc123
   ```

3. **Cancel an Execution**

   ##### `julep executions cancel`

   **Description:**  
   Cancel an existing execution.

   **Usage:**

   ```bash
   julep executions cancel --id <execution_id>
   ```

   **Options:**

   - `--id`, (required): ID of the execution to cancel.

   **Example:**

   ```bash
   julep executions cancel --id exec123
   ```

---

### Log Retrieval

Retrieve logs related to specific task executions.

#### `julep logs`

**Description:**  
Fetch and display logs for a particular task execution.

**Usage:**

```bash
julep logs --execution-id=<execution_id>
```

**Options:**

- `--execution-id`, `-e` (required): ID of the task execution to retrieve logs for.
- `--tail`, `-t` (optional): Continuously stream logs as they are generated.
- `--since=<timestamp>`, `-s` (optional): Retrieve logs generated after the specified timestamp.
- `--json`, (optional): Output the logs in JSON format.

**Example:**

```bash
julep logs --execution-id exec123 --tail
```

**Behavior:**

1. Fetches logs for the specified execution ID.
2. If `--tail` is used, streams logs in real-time.

---

### Project Assistant

Initiate a guided setup for new Julep projects.

#### `julep assistant`

**Description:**
`julep assistant` launches an interactive prompt (a "wizard" mode) that uses AI to interpret plain-English requests and transform them into valid `julep` CLI commands. Think of it as a chat-based REPL that helps you build and manage your Julep resources more intuitively.

**Usage:**
```bash
julep assistant
```

**Behavior:**
1. Opens a session where you can type natural language instructions (e.g., *"Create a GPT-4 agent named MarketingBot"*).
2. The assistant uses an LLM (Large Language Model) to suggest one or more CLI commands that match your request (e.g., `julep agents create --name "MarketingBot" --model "gpt-4"`).
3. Displays the suggested command(s) and prompts for confirmation:
   - **(Y)**: Run the command immediately, showing output in the same session.
   - **(n)**: Skip or cancel the suggestion.
   - **(edit)**: Manually revise the command prior to execution.
4. Returns to the prompt for follow-up instructions, giving you a conversational workflow (e.g., *"Now list all my tasks"*, *"Delete the agent I just created"*, etc.).

**Example Session:**
```
$ julep assistant

Welcome to Julep Assistant!
Type your request in plain English, or type 'exit' to quit.

assistant> Create a GPT-4 agent named MarketingBot
Proposed command:
julep agents create --name "MarketingBot" --model "gpt-4"

Execute? (Y/n/edit)
Y
[Running command...]
Agent created successfully (id: agent_654321)

assistant> List all tasks
Proposed command:
julep tasks list

Execute? (Y/n/edit)
Y
[Running command...]
[No tasks found]

assistant> exit
```

**Rationale & Benefits:**
- **Simplifies Onboarding**: Users can manage agents, tasks, and tools with minimal knowledge of CLI flags and syntax.
- **Conversational Guidance**: The assistant can ask clarifying questions if a request is ambiguous and recall recently created or updated resources.
- **Expandable**: Future enhancements might include richer multi-step workflows, advanced editing, and deeper project insights (e.g., referencing `julep-lock.json` state).

This feature is particularly useful for new users or those who want a quick, conversational way to build out a project without memorizing every `julep` subcommand. Simply type what you want in natural language, confirm or edit the generated commands, and let the assistant handle the rest.

### Common Commands

#### Version

##### `julep --version`, `julep -v`

**Description:**
Display the version of the CLI.

**Usage:**
```bash
julep --version
```

#### Help

##### `julep`, `julep --help`, `julep -h`

**Description:**
Display help information for the CLI.

**Usage:**
```bash
julep --help
```

#### Global Options

The following options can be used with any command:

##### Standard Input/Output Handling

The CLI supports reading from standard input (stdin) and writing to standard output (stdout) for better integration with Unix-style pipelines and scripting:

- Use `-` as a filename to read from stdin or write to stdout
- Commands that accept file inputs (like `create` and `update`) can read from stdin
- List/get commands can output directly to stdout for piping

**Examples:**

Reading definition from stdin:
```bash
cat agent.yaml | julep agents create -d -  # Read definition from stdin
echo '{"name": "MyAgent"}' | julep agents create -i -  # Read JSON from stdin
```

Piping between commands:
```bash
julep agents get abc123 | julep agents create -d -  # Clone an agent
julep agents list | jq '.[] | select(.model=="gpt-4")'  # Filter with jq
```

Writing output:
```bash
julep agents list > agents.yaml  # Save list to file
julep agents get abc123 | ssh remote-host "julep agents create -d -"  # Transfer to remote
```

**Behavior:**
- Commands detect if stdin is a pipe or terminal
- JSON/YAML format is auto-detected for stdin
- Binary data is supported for applicable inputs
- Exit codes follow Unix conventions (0=success, non-zero=error)

##### Quiet Mode

`--quiet`, `-q`: Suppress all output except errors and explicitly requested data. Useful for scripting.

**Example:**
```bash
julep agents list --quiet  # Only outputs the agent list, no status messages
```

##### Color Output

`--color`, `--no-color`: Enable or disable colored output. By default, color is:
- Enabled for TTY (interactive terminal) sessions
- Disabled for non-TTY sessions (pipes, redirects, etc.)
- Disabled if NO_COLOR environment variable is set
- Disabled if TERM=dumb

The CLI will automatically detect these conditions and adjust color output accordingly.

**Examples:**
```bash
julep agents list --no-color  # Force disable colored output
julep agents list --color     # Force enable colored output
```

**Environment Variables:**
- `NO_COLOR`: Set this to any value to disable color output
- `FORCE_COLOR`: Set this to any value to force color output

## TODO

- [x] Add `julep import agent --id <agent_id> --output=<path>`