# Julep CLI Specification

The `julep` CLI tool provides a comprehensive command-line interface for interacting with the Julep platform. It enables authentication, management of agents, tasks, and tools, project initialization, synchronization, interaction with agents via chat, task execution, log retrieval, and more. This specification outlines the commands, options, and best practices to ensure a consistent and user-friendly experience.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Configuration](#configuration)
- [Commands](#commands)
  - [Authentication](#authentication)
  - [Agent Management](#agent-management)
  - [Task Management](#task-management)
  - [Tool Management](#tool-management)
  - [Project Initialization](#project-initialization)
  - [Synchronization](#synchronization)
  - [Chat Interaction](#chat-interaction)
  - [Task Execution](#task-execution)
  - [Log Retrieval](#log-retrieval)
  - [Project Wizard](#project-wizard)
  - [Common Commands](#common-commands)
- [Best Practices](#best-practices)
- [Examples](#examples)
- [Configuration File](#configuration-file)
- [Error Handling](#error-handling)
- [Conclusion](#conclusion)

---

## Overview

The `julep` CLI is designed to streamline interactions with the Julep platform, allowing developers to efficiently manage AI agents, tasks, tools, and projects directly from the terminal. It adheres to industry-standard CLI conventions, ensuring an intuitive and predictable user experience.

---

## Installation

There are multiple ways to install the `julep` CLI:

1. **Using pipx:**

    ```bash
    pipx install julep
    ```

2. **Using npm:**

    Ensure you have [Node.js](https://nodejs.org/) installed. Then, install the `julep` CLI globally using `npm`:

    ```bash
    npm install -g @julep/cli
    ```

3. **Using yarn:**

    ```bash
    yarn global add @julep/cli
    ```

---

## Configuration

The CLI stores configuration data, such as the API key, in `~/.config/julep/config.yml`. After authentication, this file is created automatically.

---

## Commands

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

   - `--name`, `-n` (required): Name of the agent.
   - `--model`, `-m` (required): Model to be used by the agent (e.g., `gpt-4`).
   - `--about`, `-a` (optional): Description of the agent.
   - `--dry-run`, `-d` (optional): Simulate agent creation without making API calls.

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
   julep agents update --id <agent_id> [--name "New Name"] [--model "New Model"] [--about "New Description"]
   ```

   **Options:**

   - `--id`, `-i` (required): ID of the agent to update.
   - `--name`, `-n` (optional): New name for the agent.
   - `--model`, `-m` (optional): New model for the agent.
   - `--about`, `-a` (optional): New description for the agent.
   - `--dry-run`, `-d` (optional): Simulate agent update without making API calls.

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
   julep agents delete --id <agent_id>
   ```

   **Options:**

   - `--id`, `-i` (required): ID of the agent to delete.
   - `--dry-run`, `-d` (optional): Simulate agent deletion without making API calls.

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
   julep agents list [--metadata-filter "criteria"]
   ```

   **Options:**

   - `--metadata-filter`, `-f` (optional): Filter agents based on specific criteria (e.g., name, model).
   - `--json`, `-j` (optional): Output the list in JSON format.

   **Example:**

   ```bash
   julep agents list --metadata-filter "model=gpt-4"
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
   julep tasks create --name "Task Name" --agent-id <agent_id> --definition "path/to/task.yaml"
   ```

   **Options:**

   - `--name`, `-n` (optional): Name of the task (if not provided, the name will be the file name of the definition).
   - `--description`, `-d` (optional): Description of the task (if not provided, the description will be the file name of the definition).
   - `--agent-id`, `-a` (required): ID of the agent the task is associated with.
   - `--definition`, `-d` (required): Path to the task definition YAML file.
   - `--dry-run`, `-r` (optional): Simulate task creation without making API calls.

   **Example:**

   ```bash
   julep tasks create --name "Generate Story" --agent-id abc123 --definition ./tasks/generate_story.yaml
   ```

2. **Update a Task**

   ##### `julep tasks update`

   **Description:**  
   Update an existing task's details.

   **Usage:**

   ```bash
   julep tasks update --id <task_id> [--name "New Name"] [--definition "new/path/to/task.yaml"]
   ```

   **Options:**

   - `--id`, `-i` (required): ID of the task to update.
   - `--name`, `-n` (optional): New name for the task.
   - `--definition`, `-d` (optional): Path to the updated task definition YAML file.
   - `--dry-run`, `-r` (optional): Simulate task update without making API calls.

   **Example:**

   ```bash
   julep tasks update --id task456 --name "Advanced Story Generation"
   ```

3. **Delete a Task**

   ##### `julep tasks delete`

   **Description:**  
   Delete an existing task.

   **Usage:**

   ```bash
   julep tasks delete --id <task_id>
   ```

   **Options:**

   - `--id`, `-i` (required): ID of the task to delete.
   - `--dry-run`, `-d` (optional): Simulate task deletion without making API calls.

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
   julep tasks list [--agent-id <agent_id>] [--filter "criteria"]
   ```

   **Options:**

   - `--agent-id`, `-a` (optional): Filter tasks by associated agent ID.
   - `--filter`, `-f` (optional): Additional filter criteria (e.g., status).
   - `--json`, `-j` (optional): Output the list in JSON format.

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
   julep tools create --name "Tool Name" --type <type> --agent-id <agent_id> --config "path/to/config.yaml"
   ```

   **Options:**

   - `--name`, `-n` (required): Name of the tool.
   - `--type`, `-t` (required): Type of the tool (`integration`, `api_call`, `function`, `system`).
   - `--agent-id`, `-a` (required): ID of the agent the tool is associated with.
   - `--config`, `-c` (required): Path to the tool configuration YAML file.
   - `--dry-run`, `-d` (optional): Simulate tool creation without making API calls.

   **Example:**

   ```bash
   julep tools create --name "Web Search" --type integration --agent-id abc123 --config ./tools/web_search.yaml
   ```

2. **Update a Tool**

   ##### `julep tools update`

   **Description:**  
   Update an existing tool's details.

   **Usage:**

   ```bash
   julep tools update --id <tool_id> [--name "New Name"] [--config "new/path/to/config.yaml"]
   ```

   **Options:**

   - `--id`, `-i` (required): ID of the tool to update.
   - `--name`, `-n` (optional): New name for the tool.
   - `--config`, `-c` (optional): Path to the updated tool configuration YAML file.
   - `--dry-run`, `-d` (optional): Simulate tool update without making API calls.

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
   julep tools delete --id <tool_id>
   ```

   **Options:**

   - `--id`, `-i` (required): ID of the tool to delete.
   - `--dry-run`, `-d` (optional): Simulate tool deletion without making API calls.

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
   julep tools list [--agent-id <agent_id>] [--type <type>]
   ```

   **Options:**

   - `--agent-id`, `-a` (optional): Filter tools by associated agent ID.
   - `--type`, `-t` (optional): Filter tools by type (`integration`, `api_call`, `function`, `system`).
   - `--json`, `-j` (optional): Output the list in JSON format.

   **Example:**

   ```bash
   julep tools list --agent-id abc123 --type integration
   ```

---

### Project Initialization

Initialize a new Julep project using predefined templates.

#### `julep init`

**Description:**  
Initialize a new Julep project by copying a template from the library repository.

**Usage:**

```bash
julep init --template=<template_name> [--destination=<path>]
```

**Options:**

- `--template`, `-t` (required): Name of the template to use (e.g., `hello-world`).
- `--destination`, `-d` (optional): Destination directory for the initialized project (default: current directory).

**Example:**

```bash
julep init --template=hello-world --destination=./my-julep-project
```

**Behavior:**

1. Copies the specified template folder from the `/library` repository to the destination directory.
2. Ensures the destination directory contains a `julep.toml` file, validating it as a valid Julep package.

---

### Synchronization

Synchronize local directories with Julep packages.

#### `julep sync`

**Description:**  
Synchronize the local Julep package with the Julep platform.

**Usage:**

```bash
julep sync --source=<path>
```

**Options:**

- `--source`, `-s` (required): Source directory containing the Julep package (must include `julep.toml`).
- `--force`, `-f` (optional): Force synchronization even if discrepancies are detected.
- `--dry-run`, `-d` (optional): Simulate synchronization without making API calls.

**Example:**

```bash
julep sync --source=./my-julep-project
```

**Behavior:**

1. Validates the presence of `julep.toml` in the source directory.
2. Synchronizes the package with the Julep backend, uploading any changes.
3. Provides feedback on the synchronization status.

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
- `--history`, `-h` (optional): Load previous chat history from a file.
- `--save-history`, `-s` (optional): Save chat history to a specified file.

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
- `--input`, `-i` (required): JSON string representing the input for the task.
- `--dry-run`, `-d` (optional): Simulate task execution without making API calls.
- `--output=<path>`, `-o` (optional): Save the task output to a specified file.

**Example:**

```bash
julep run --task "Generate Story" --input '{"idea": "A cat who learns to fly"}'
```

**Behavior:**

1. Submits the task for execution with the provided input.
2. Monitors the execution status in real-time.
3. Outputs the final result upon completion.

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

**Example:**

```bash
julep logs --execution-id exec123 --tail
```

**Behavior:**

1. Fetches logs for the specified execution ID.
2. If `--tail` is used, streams logs in real-time.
3. Supports filtering logs based on the provided timestamp.

---

### Project Wizard

Initiate a guided setup for new Julep projects.

#### `julep new` or `julep wizard`

**Description:**  
Launch an interactive wizard to set up a new Julep project with customized configurations.

**Usage:**

```bash
julep new
```

or

```bash
julep wizard
```

**Options:**

- `--template`, `-t` (optional): Specify a template to base the project on.
- `--interactive`, `-i` (optional): Force interactive mode even if default options are available.

**Example:**

```bash
julep new
```

**Behavior:**

1. Guides the user through a series of prompts to configure the new project.
2. Allows customization of agent settings, task definitions, and tool integrations.
3. Generates necessary configuration files and directory structures based on user input.

---

### Common Commands

#### Version

##### `julep version`, `julep --version`, `julep -v`

**Description:**  
Display the current version of the Julep CLI.

**Usage:**

```bash
julep --version
```

**Output:**

```bash
julep CLI version 1.2.3
```

#### Help

##### `julep help`, `julep --help`, `julep -h`

**Description:**  
Display help information for the CLI or specific commands.

**Usage:**

```bash
julep --help
```

**Behavior:**

- Provides detailed information about commands, subcommands, and options.
- Shows usage examples and descriptions for each option.

---

## Best Practices

The `julep` CLI adheres to the following best practices to ensure a consistent and user-friendly experience:

1. **Default Options:**  
   Commands that can have default values provide them to simplify usage.

2. **Readable Option Names with Short Aliases:**  
   Long, descriptive option names are paired with short aliases (e.g., `--agent` and `-a`) for convenience.

3. **Consistent CLI Patterns:**  
   The CLI follows common command-line conventions, making it intuitive for users familiar with industry standards.

4. **Explicit File Identification:**  
   Options are available to explicitly specify files or directories to process, reducing ambiguity.

5. **No Positional Options:**  
   All options are specified using flags, avoiding positional arguments to enhance flexibility.

6. **Comprehensive Help Command:**  
   Accessible via `help`, `--help`, or `-h`, providing extensive guidance on commands and usage.

7. **Version Command:**  
   Accessible via `version`, `--version`, or `-v`, allowing users to check the CLI version easily.

8. **Real-Time Feedback:**  
   The CLI provides immediate feedback for operations, ensuring users are informed about the progress and outcomes.

9. **Dry-Run Options:**  
   Commands that perform actions with side effects offer `--dry-run` options to simulate actions without making changes.

10. **Error Recovery for Long-Running Operations:**  
    For operations that may take time, mechanisms are in place to resume from failure points if possible.

11. **Consistent Exit Codes:**  
    The CLI exits with non-zero status codes only when errors occur, enabling seamless integration with scripts and automation tools.

12. **Proper Output Channels:**  
    Useful information is written to `stdout`, while warnings and errors are sent to `stderr`, facilitating better logging and debugging.

13. **Minimal CLI Script:**  
    The CLI script is kept lightweight, delegating tasks to submodules or external processes to maintain simplicity.

14. **Reserved Stack Traces:**  
    Stack traces are only displayed for truly exceptional cases, keeping regular user output clean and focused.

---

## Examples

### Authenticate with API Key

```bash
julep auth --api-key your_julep_api_key
```

### Create a New Agent

```bash
julep agents create --name "Researcher" --model "gpt-4" --about "An agent that conducts research and summarizes findings."
```

### List All Agents

```bash
julep agents list
```

### Update an Existing Agent

```bash
julep agents update --id abc123 --name "Advanced Researcher" --model "gpt-4.5"
```

### Delete an Agent

```bash
julep agents delete --id abc123
```

### Initialize a New Project from Template

```bash
julep init --template=hello-world --destination=./my-new-project
```

### Synchronize Local Project with Julep

```bash
julep sync --source=./my-new-project
```

### Interact with an Agent via Chat

```bash
julep chat --agent "Researcher"
```

### Execute a Task with Input

```bash
julep run --task "Generate Report" --input '{"topic": "Climate Change"}'
```

### Retrieve Logs for an Execution

```bash
julep logs --execution-id exec789 --tail
```

### Launch the Project Wizard

```bash
julep new
```

---

## Configuration File

The CLI configuration is stored in `~/.config/julep/config.yml`. Below is an example configuration file:

```yaml
api_key: your_julep_api_key
environment: production
default_agent: "Storyteller"
```

**Fields:**

- `api_key`: Your Julep API key for authentication.
- `environment`: Specifies the environment (`production`, `development`, etc.).
- `default_agent`: Sets a default agent to use for commands that require an agent.

---

## Error Handling

The CLI follows robust error handling practices to ensure clarity and reliability:

- **Non-zero Exit Codes:**  
  The CLI exits with a non-zero status code only when an error occurs, allowing integration with automation tools and scripts.

- **Clear Error Messages:**  
  Errors are communicated clearly to the user, specifying the issue and potential resolutions.

- **Dry-Run Validation:**  
  Before performing actions, the CLI validates inputs and configurations, especially when `--dry-run` is used.

- **Recovery Options:**  
  For long-running operations, the CLI attempts to resume from failure points whenever possible, minimizing disruption.

**Example Error Message:**

```
Error: Agent with ID abc123 not found.
```

---

## Conclusion

The `julep` CLI is meticulously designed to provide an efficient and intuitive interface for managing AI agents, tasks, tools, and projects within the Julep platform. By adhering to industry best practices, it ensures a seamless user experience, facilitating the development and deployment of advanced AI workflows with ease.

For further assistance or to contribute to the CLI's development, refer to the [Julep Documentation](https://docs.julep.ai/) or join the [Julep Discord Community](https://discord.com/invite/JTSBGRZrzj).

## Notes (Draft):
- `julep auth` command:
  - Show the user where to get api key if prompted to enter one (e.g. you can get it from here...).
  - Verify that the api-key is a valid jwt.
  - Have a `--skip-verify` flag to skip verification of the API key.
  - Ideally: Have a `/me` endpoint to verify the API key from the Julep backend.
  - Save the `developer_id` in the config file too.

