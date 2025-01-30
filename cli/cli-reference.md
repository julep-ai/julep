# `julep`

Command line interface for the Julep platform

**Usage**:

```console
$ julep [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--no-color`: Disable colored output  [default: True]
* `-q, --quiet`: Suppress all output except errors and explicitly requested data
* `-v, --version`: Show version and exit
* `--help`: Show this message and exit.

**Commands**:

* `tui`: Open Textual TUI.
* `auth`: Authenticate with the Julep platform.
* `chat`: Initiate an interactive chat session with...
* `init`: Initialize a new Julep project by copying...
* `logs`: Log the output of an execution.
* `ls`: List synced entities in a julep source...
* `run`: Run a defined task with specified input...
* `sync`: Synchronize local package with Julep platform
* `agents`: Manage AI agents
* `tasks`: Manage tasks
* `tools`: Manage tools
* `import`: Import entities from the Julep platform
* `executions`: Manage executions

## `julep tui`

Open Textual TUI.

**Usage**:

```console
$ julep tui [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `julep auth`

Authenticate with the Julep platform.

Saves your API key to ~/.config/julep/config.yml for use with other commands.
The API key can be found in your Julep account settings.

**Usage**:

```console
$ julep auth [OPTIONS]
```

**Options**:

* `-k, --api-key TEXT`: Your Julep API key for authentication  [env var: JULEP_API_KEY]
* `-e, --environment TEXT`: Environment to use (defaults to production)  [default: production]
* `--help`: Show this message and exit.

## `julep chat`

Initiate an interactive chat session with a specified AI agent.

The chat session runs in the terminal, allowing real-time conversation with the agent.

**Usage**:

```console
$ julep chat [OPTIONS]
```

**Options**:

* `-a, --agent TEXT`: ID or name of the agent to chat with  [required]
* `-s, --situation TEXT`: Situation to chat about
* `--settings LOADS`: Chat settings as a JSON string
* `--help`: Show this message and exit.

## `julep init`

Initialize a new Julep project by copying a template from the library repository.

This will:
1. Copy the specified template folder from the /library repository
2. Create a new project in the destination directory
3. Ensure the destination contains a valid julep.yaml file

**Usage**:

```console
$ julep init [OPTIONS]
```

**Options**:

* `-t, --template TEXT`: Name of the template to use from the library repository  [default: hello-world]
* `-p, --path PATH`: Destination directory for the initialized project (default: current directory)  [default: /Users/hamadasalhab/Documents/repos/julep-ai/julep/cli]
* `-y, --yes`: Skip confirmation prompt
* `--help`: Show this message and exit.

## `julep logs`

Log the output of an execution.

**Usage**:

```console
$ julep logs [OPTIONS]
```

**Options**:

* `-e, --execution-id TEXT`: ID of the execution to log  [required]
* `-t, --tail`: Whether to tail the logs
* `--help`: Show this message and exit.

## `julep ls`

List synced entities in a julep source project.

**Usage**:

```console
$ julep ls [OPTIONS]
```

**Options**:

* `-s, --source PATH`: Path to list  [default: /Users/hamadasalhab/Documents/repos/julep-ai/julep/cli]
* `--help`: Show this message and exit.

## `julep run`

Run a defined task with specified input parameters

**Usage**:

```console
$ julep run [OPTIONS]
```

**Options**:

* `-t, --task TEXT`: ID or name of the task to execute  [required]
* `--input TEXT`: JSON string representing the input for the task (defaults to {})
* `--input-file PATH`: Path to a file containing the input for the task
* `--wait`: Wait for the task to complete before exiting, stream logs to stdout
* `--help`: Show this message and exit.

## `julep sync`

Synchronize local package with Julep platform

**Usage**:

```console
$ julep sync [OPTIONS]
```

**Options**:

* `-s, --source PATH`: Source directory containing julep.yaml  [default: /Users/hamadasalhab/Documents/repos/julep-ai/julep/cli]
* `--force-local`: Force local state to match remote
* `--force-remote`: Force remote state to match local
* `-d, --dry-run`: Simulate synchronization without making changes
* `--help`: Show this message and exit.

## `julep agents`

Manage AI agents

**Usage**:

```console
$ julep agents [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `create`: Create a new AI agent.
* `update`: Update an existing AI agent&#x27;s details
* `delete`: Delete an existing AI agent
* `list`: List all AI agents or filter based on...
* `get`: Get an agent by its ID

### `julep agents create`

Create a new AI agent. Either provide a definition file or use the other options.

**Usage**:

```console
$ julep agents create [OPTIONS]
```

**Options**:

* `-n, --name TEXT`: Name of the agent
* `-m, --model TEXT`: Model to be used by the agent
* `-a, --about TEXT`: Description of the agent
* `--default-settings TEXT`: Default settings for the agent (JSON string)
* `--metadata TEXT`: Metadata for the agent (JSON string)
* `--instructions TEXT`: Instructions for the agent, can be specified multiple times
* `-d, --definition TEXT`: Path to an agent definition file
* `--help`: Show this message and exit.

### `julep agents update`

Update an existing AI agent&#x27;s details

**Usage**:

```console
$ julep agents update [OPTIONS]
```

**Options**:

* `--id TEXT`: ID of the agent to update  [required]
* `-n, --name TEXT`: New name for the agent
* `-m, --model TEXT`: New model for the agent
* `-a, --about TEXT`: New description for the agent
* `--metadata TEXT`: Metadata for the agent (JSON string)
* `--default-settings TEXT`: Default settings for the agent (JSON string)
* `--instructions TEXT`: Instructions for the agent, can be specified multiple times
* `--help`: Show this message and exit.

### `julep agents delete`

Delete an existing AI agent

**Usage**:

```console
$ julep agents delete [OPTIONS]
```

**Options**:

* `--id TEXT`: ID of the agent to delete  [required]
* `-f, --force`: Force deletion without confirmation
* `--help`: Show this message and exit.

### `julep agents list`

List all AI agents or filter based on metadata

**Usage**:

```console
$ julep agents list [OPTIONS]
```

**Options**:

* `--metadata-filter TEXT`: Filter agents based on metadata criteria (JSON string)
* `--json`: Output the list in JSON format
* `--help`: Show this message and exit.

### `julep agents get`

Get an agent by its ID

**Usage**:

```console
$ julep agents get [OPTIONS]
```

**Options**:

* `--id TEXT`: ID of the agent to retrieve  [required]
* `--json`: Output in JSON format
* `--help`: Show this message and exit.

## `julep tasks`

Manage tasks

**Usage**:

```console
$ julep tasks [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `create`: Create a new task for an agent.
* `update`: Update an existing task&#x27;s details
* `list`: List all tasks or filter based on criteria

### `julep tasks create`

Create a new task for an agent.

If other options are provided alongside the definition file, they will override values in the definition.

**Usage**:

```console
$ julep tasks create [OPTIONS]
```

**Options**:

* `-a, --agent-id TEXT`: ID of the agent the task is associated with  [required]
* `-d, --definition TEXT`: Path to the task definition YAML file  [required]
* `-n, --name TEXT`: Name of the task (if not provided, uses the definition file name)
* `--description TEXT`: Description of the task (if not provided, uses the definition file name)
* `--metadata TEXT`: JSON metadata for the task
* `--inherit-tools`: Inherit tools from the associated agent
* `--help`: Show this message and exit.

### `julep tasks update`

Update an existing task&#x27;s details

**Usage**:

```console
$ julep tasks update [OPTIONS]
```

**Options**:

* `-a, --agent-id TEXT`: ID of the agent the task is associated with  [required]
* `--id TEXT`: ID of the task to update  [required]
* `-n, --name TEXT`: New name for the task
* `--description TEXT`: New description for the task
* `-d, --definition TEXT`: Path to the updated task definition YAML file
* `--metadata TEXT`: JSON metadata for the task
* `--inherit-tools`: Inherit tools from the associated agent
* `--help`: Show this message and exit.

### `julep tasks list`

List all tasks or filter based on criteria

**Usage**:

```console
$ julep tasks list [OPTIONS]
```

**Options**:

* `-a, --agent-id TEXT`: Filter tasks by associated agent ID
* `-j, --json`: Output the list in JSON format
* `--help`: Show this message and exit.

## `julep tools`

Manage tools

**Usage**:

```console
$ julep tools [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `create`: Create a new tool for an agent.
* `update`: Update an existing tool&#x27;s details.
* `delete`: Delete an existing tool.
* `list`: List all tools or filter based on criteria.

### `julep tools create`

Create a new tool for an agent.

Requires either a definition file or direct parameters. If both are provided,
command-line options override values from the definition file.

**Usage**:

```console
$ julep tools create [OPTIONS]
```

**Options**:

* `-a, --agent-id TEXT`: ID of the agent the tool is associated with  [required]
* `-d, --definition TEXT`: Path to the tool configuration YAML file  [required]
* `-n, --name TEXT`: Name of the tool (if not provided, uses filename from definition)
* `--help`: Show this message and exit.

### `julep tools update`

Update an existing tool&#x27;s details.

Updates can be made using either a definition file or direct parameters.
If both are provided, command-line options override values from the definition file.

**Usage**:

```console
$ julep tools update [OPTIONS]
```

**Options**:

* `-a, --agent-id TEXT`: ID of the agent the tool is associated with  [required]
* `--id TEXT`: ID of the tool to update  [required]
* `-d, --definition TEXT`: Path to the updated tool configuration YAML file
* `-n, --name TEXT`: New name for the tool
* `--help`: Show this message and exit.

### `julep tools delete`

Delete an existing tool.

By default, prompts for confirmation unless --force is specified.

**Usage**:

```console
$ julep tools delete [OPTIONS]
```

**Options**:

* `-a, --agent-id TEXT`: ID of the agent the tool is associated with  [required]
* `--id TEXT`: ID of the tool to delete  [required]
* `-f, --force`: Force the deletion without prompting for confirmation
* `--help`: Show this message and exit.

### `julep tools list`

List all tools or filter based on criteria.

Either --agent-id or --task-id must be provided to filter the tools list.

**Usage**:

```console
$ julep tools list [OPTIONS]
```

**Options**:

* `-a, --agent-id TEXT`: Filter tools by associated agent ID
* `--json`: Output the list in JSON format
* `--help`: Show this message and exit.

## `julep import`

Import entities from the Julep platform

**Usage**:

```console
$ julep import [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `agent`: Import an agent from the Julep platform.

### `julep import agent`

Import an agent from the Julep platform.

**Usage**:

```console
$ julep import agent [OPTIONS]
```

**Options**:

* `-i, --id TEXT`: ID of the agent to import  [required]
* `-s, --source PATH`: Path to the source directory. Defaults to current working directory  [default: /Users/hamadasalhab/Documents/repos/julep-ai/julep/cli]
* `-o, --output PATH`: Path to save the imported agent. Defaults to &lt;project_dir&gt;/src/agents
* `-y, --yes`: Skip confirmation prompt
* `--help`: Show this message and exit.

## `julep executions`

Manage executions

**Usage**:

```console
$ julep executions [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `create`: Create a new execution.

### `julep executions create`

Create a new execution.

**Usage**:

```console
$ julep executions create [OPTIONS]
```

**Options**:

* `--task-id TEXT`: ID of the task to execute  [required]
* `--input TEXT`: Input for the execution  [required]
* `--help`: Show this message and exit.

