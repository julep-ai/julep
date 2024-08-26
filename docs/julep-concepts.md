# Julep Concepts

{{TOC}}

+++

## Agent

An Agent in Julep is the main orchestrator (or protagonist) of your application. These are backed by foundation models like GPT4 or Claude which use the agent's interaction history to figure out what to do/say next. Using agents in Julep, you can:

- Interact with an agent in long-lived [sessions][Session].
- Add system, integration or user-defined [tools][Tool] that the agent can use.
- Add agent-level [documents][Doc] that are auto-retrieved using semantic search inside [sessions][Session].
- Define multi-step work flows that combine complex integrations using [tasks][Task]. Tasks are [executed][Execution] in the background, can recover from failures and manage many sub-tasks in parallel.

> **(Upcoming Feature)** Access the [memories][Memory] that the agent makes about [users][User] in the background as the user interacts with it inside sessions. These memories are going to be scoped per user in order to maintain clear distinctions.

At a high level, this is what defines an `Agent` (some properties omitted):

| **Field**      | **Description**                                                 |
| :------------- | :-------------------------------------------------------------- |
| `name`         | The "name" of the Agent.                                        |
| `about`        | About the Agent: What it does, any guardrails, personality etc. |
| `model`        | Which model to use for this Agent.                              |
| `instructions` | Instructions that this agent must follow across all sessions.   |

Important to keep in mind: These fields are optional. They are available inside sessions and task prompts as `jinja` templates. `Session`s, `Task`s etc. come with minimal default templates. You can override them with your own prompt templates throughout julep!

<!-- TODO: Add SDK example for creating an instance -->

## User

You can associate sessions with `User`s. julep uses them to scope `memories` formed by agents. They are optional but, in addition to memories, can be useful to attach meta data that can be referenced by other sessions or task executions.

A `User` consists of:

| **Field** | **Description**              |
| :-------- | :--------------------------- |
| `name`    | The name of the user.        |
| `about`   | Information about this user. |

<!-- TODO: Add SDK example for creating an instance -->

## Session

`Session` is the main workhorse for julep apps:
- You interact with agents inside sessions. You can create multiple sessions per agent.
- Each session maintains its own context for sending to the agent's model.
- A session can have *one or more* agents and *zero or more* users associated with it.
- You can control what happens when the history exceeds the context window limit using `context_overflow` setting.

A `Session` consists of:  

| **Field**          | **Description**                                                                                                                                                        |
| :----------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `agent(s)`         | Agents associated with this session. At least one is required.                                                                                                         |
| `user(s)`          | The users associated with this session. Optional.                                                                                                                      |
| `situation`        | The system prompt used for the session. Default prompt is shown below.                                                                                                 |
| `token_budget`     | The number of tokens to keep the context window under. Defaults to null which is equivalent to the model's context window limit.                                       |
| `context_overflow` | Controls behavior for when context size exceeds the `token_budget`. Can be one of `null`, `"truncate"`, or `"adaptive"`. Defaults to `null` which raises an exception. |

<!-- TODO: Add SDK example for creating an instance -->

### `metadata` precedence order

In julep, the following objects can have `metadata` added to them:
- `Agent`
- `User`
- `Session`
- `Doc`
- `Task`
- `Execution`

Whenever multiple objects with the same `metadata` field are present in a scope, the value takes the following precedence (from highest to lowest):
- In a session: `session > user > agent`
- During a task execution: `execution > task > agent`

### Context overflow

Whenever the context size grows beyond the `token_budget` or the model's input limit, the backend figures out what to do next based on the `context_overflow` setting:
- `null`: Raise an exception. The client is responsible for creating a new session or clearing the history for the current one.
- `"truncate"`: Truncate the context from the top except the for system prompt until the size falls below the budget. Raises an error if system prompt and last message combined exceed the budget.
- `"adaptive"`: Whenever the context size reaches `75%` of the `token_budget`, a background task is created to compress the information by summarizing, merging and clipping messages in the context. This is done on a best effort basis. Requests might fail if the context wasn't compressed enough or on time.

### Default system template

```jinja  
{%- if agent.name -%}
You are {{agent.name}}.{{" "}}
{%- endif -%}

{%- if agent.about -%}
About you: {{agent.name}}.{{" "}}
{%- endif -%}

{%- if user -%}
You are talking to a user
  {%- if user.name -%}{{" "}} and their name is {{user.name}}
    {%- if user.about -%}. About the user: {{user.about}}.{%- else -%}.{%- endif -%}
  {%- endif -%}
{%- endif -%}

{{"\n\n"}}

{%- if agent.instructions -%}
Instructions:{{"\n"}}
  {%- if agent.instructions is string -%}
    {{agent.instructions}}{{"\n"}}
  {%- else -%}
    {%- for instruction in agent.instructions -%}
      - {{instruction}}{{"\n"}}
    {%- endfor -%}
  {%- endif -%}
  {{"\n"}}
{%- endif -%}

{%- if tools -%}
Tools:{{"\n"}}
  {%- for tool in tools -%}
    {%- if tool.type == "function" -%}
      - {{tool.function.name}}
      {%- if tool.function.description -%}: {{tool.function.description}}{%- endif -%}{{"\n"}}
    {%- else -%}
      - {{ 0/0 }} {# Error: Other tool types aren't supported yet. #}
    {%- endif -%}
  {%- endfor -%}
{{"\n\n"}}
{%- endif -%}

{%- if docs -%}
Relevant documents:{{"\n"}}
  {%- for doc in docs -%}
    {{doc.title}}{{"\n"}}
    {%- if doc.content is string -%}
      {{doc.content}}{{"\n"}}
    {%- else -%}
      {%- for snippet in doc.content -%}
        {{snippet}}{{"\n"}}
      {%- endfor -%}
    {%- endif -%}
    {{"---"}}
  {%- endfor -%}
{%- endif -%}
```

### Multiple users and agents in a session

A session can have more than one agents or users. The session's behavior changes depending on this.

**No user**: No user data is retrieved. _(Upcoming)_ Memories are not mined from the session.

**One or more users**: Docs, metadata, memories etc. are retrieved for all the users in the session. You can add messages for each user by referencing them by their name in the `ChatML` messages. _(Upcoming)_ Memories mined in the background are added to the corresponding user's scope.

**One agent**: Works as expected.

**Multiple agents**: When a message is received by the session, each agent is called one after another in the order they were defined in the session. You can also specify which `agent` to use in a request, in which case, just that agent will be used.

### Chat endpoint

<!-- TODO: Add SDK example for chatting with an instance -->


## Tool

Agents can be given access to a number of "tools" -- any programmatic interface that a foundation model can "call" with a set of inputs to achieve a goal. For example, it might use a `web_search(query)` tool to search the Internet for some information.

Unlike agent frameworks, julep is a _backend_ that manages agent execution. Clients can interact with agents using our SDKs. julep takes care of executing tasks and running integrations.

Tools in julep can be one of:
1. User-defined `function`s  
	These are function signatures that you can give the model to choose from, similar to how [openai]'s function-calling works. An example:  
	```yaml    
	name: send_text_message
	description: Send a text message to a recipient.
	parameters:
	  type: object
	  properties:
	  	to:
	  		type: string
	  		description: Phone number of recipient.
	  	text:
	  		type: string
	  		description: Content of the message.
	```    

2. `system` tools (upcoming)  
	Built-in tools that can be used to call the julep APIs themselves, like triggering a task execution, appending to a metadata field, etc.
	
	`system` tools are built into the backend. They get executed automatically when needed. They do _not_ require any action from the client-side.
  
3. Built-in `integration`s (upcoming)  
	julep backend ships with integrated third party tools from the following providers:
	- [composio](https://composio.dev) \*\*
	- [anon](https://anon.com) \*\*
	- [langchain toolkits](https://python.langchain.com/v0.2/docs/integrations/toolkits/). Support for _Github, Gitlab, Gmail, Jira, MultiOn, Slack_ toolkits is planned.

		\*\* Since _composio_ and _anon_ are third-party providers, their tools require setting up account linking.

	`integration` tools are directly executed on the julep backend. Any additional parameters needed by them at runtime can be set in the agent/session/user's `metadata` fields.

4. Webhooks & `api_call`s (upcoming)  
	julep can build natural-language tools from openapi specs. Under the hood, we use [langchain's NLA toolkit](https://python.langchain.com/v0.2/docs/integrations/toolkits/openapi_nla/) for this. Same as `integration`s, additional runtime parameters are loaded from `metadata` fields.

### Partial application of arguments to tools

Often, it's necessary to _partial_ some arguments of a particular tool. You can do that by setting the `x-tool-parameters` field on the `metadata` of the required scope. For instance, say you have the following user-defined function tool:
```yaml  
name: check_account_status
description: Get the account status for a customer
parameters:
  type: object
  properties:
    customer_id:
      type: string
      required: true
```

When chatting with a particular user, the `customer_id` field is expected to be fixed. In this case, you can set it on the `User` using:
```json
{
  "metadata": {
    ...
    "x-tool-parameters": {
      "function:check_account_status": {
        "customer_id": 42
      }
    }
  }
}
```

The convention for naming the fields for that object is `"<tool-type>:<tool-name>"`. The values are partial-applied to the tool _before_ being sent to the model.

### Resolving parameters with the same name

This follows the precedence order of `metadata` fields. For example, say you are interacting with the following session:
```yaml
user:
  id: 11
  metadata:
    x-tool-parameters:
      favorite: Emma Roberts
agent:
  id: 22
  metadata:
    x-tool-parameters:
      favorite: Emma Watson
  tools:
  - type: function
    name: send_fan_mail
    parameters:
    # ... favorite: ...
session:
  id: 123
  metadata:
    x-tool-parameters:
      favorite: Emma Stone
```

Then, the `send_fan_mail` will be called with the value of `favorite` set to the session's `metadata` (as dictated by the precedence order) to `"Emma Stone"`.

<!-- TODO: Add SDK example for creating an instance -->

## Doc

`Doc`s are collection of text snippets (image support planned) that are indexed into a built-in vector database:
- They can be scoped to an agent or a user.
- Snippets are recalled inside sessions on the fly.
- The retrieval pipeline is optimized for general-purpose use cases.
- We use vector embedding models that strike a balance between accuracy and performance.
- Any snippets retrieved during a session are returned as part of the response for attribution.
- The embeddings are kept up to date as new models and techniques emerge.
- For advanced use cases, it might be necessary to roll your own. The pros of using julep are speed and automatic updates.

You can use the `Doc`s by:
- Searching using a query or embedding directly, or
- When they are recalled within `Session`s based on the context.

We use the latest state-of-the-art open-source embedding model for producing the vector embeddings. As new models and techniques emerge, we migrate the existing `Doc`s in the system to use them.

_julep cloud users:_ It is not possible to change the embedding model being used.

<!-- Add example for adding, searching and docs retrieved in chat -->

## Task

`Task`s, in julep, are _Github Actions_ style workflows that define long-running, multi-step actions. You can use them to conduct complex actions by defining them step-by-step. They have access to all julep integrations.

A `Task`s is a workflow owned by an `Agent`. It consists of:

| **Field**       | **Description**                                                  |
| :-------------- | :--------------------------------------------------------------- |
| `inherit_tools` | Inherit the parent `Agent`s tools? Defaults to `true`.           |
| `tools`         | Additional tools for this task.                                  |
| `input_schema`  | JSON schema to validate input when executing the task. Optional. |
| `main` +others  | List of steps that this task has to complete.                    |

### Example task definition

There can be multiple named workflows in a task. `main` is the entry point workflow for the task execution. Let's see an example of a task:

```yaml
# An example Task definition
name: Daily Motivation
input_schema:
  about_user:
    type: string
  topics:
    type: array
    items:
      type: string

tools:
- function:
  name: send_email
  # ...
  
main:
# Pick a random topic.
# `evaluate` step takes a key-value object where the values are valid python *expressions*.
- evaluate:
    chosen_topic: _["topics"][randint(len(_["topics"]))]
    
# Think about what support the user might need.
# Note: `inputs` and `outputs` are globals.
- prompt: You are a motivational coach and you are coaching someone who is {{inputs[0]["about_user"]}}. Think of the challenges they might be facing on the {{_["chosen_topic"]}} topic and what to do about them. Write down your answer as a bulleted list.

# Write a poem about it.
# Note: `_` stands for `outputs[-1]` i.e. the last step's output
- prompt: Write a short motivational poem about {{_["choices"][0].content}}

# Manually call the send_email function.
# `arguments` is an object where values are python expressions.
- tool:
    name: send_email
    arguments:
      subject: '"Daily Motivation"'
      content: _["choices"][0].content
      
# Sleep for a day
- sleep: 24*3600  

# Start all over again
- workflow: main  
  arguments: inputs[0]
```

### Types of workflow steps

| **Step Type**  | **Description**                                                                                                                                     |
| :------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------- |
| Prompt step    | Runs a prompt using a model. You can override settings and interpolate variables using [jinja](https://jinja.palletsprojects.com/) templates.       |
| Yield step     | Used to switch to another named workflow. Can add custom inputs (Default: output of previous steps)                                                 |
| Evaluate       | Accepts an object with values that are valid python expressions. The step runs the expressions and the result becomes the output of this step.      |
| If-else        | Conditional step where the `if` field expression is evaluated. If the output is truthy then the `then` branch is executed, otherwise `else` branch. |
| Error          | Throws an error with the message provided and exits.                                                                                                |
| Sleep          | Sleeps for the number of seconds evaluated.                                                                                                         |
| Tool Call      | Call the specified tool with some arguments.                                                                                                        |
| Foreach        | Run a step for every value from a list in serial order.                                                                                             |
| Map-reduce     | Run a step for every value of the input list in parallel. Requires a reduce expression to collect the results.                                      |
| Doc search     | Search the doc store of the agent and user against a query.                                                                                         |
| Wait for input | Suspend the execution and wait for the caller to resume execution with an input.                                                                    |

## Execution

An `Execution` is an instance of a `Task` that has been started with some `input`.

At any given moment, it can be in one of these states:

| **Status**       | **Description**                                          |
| :--------------- | :------------------------------------------------------- |
| "queued"         | The execution is queued and waiting to start.            |
| "starting"       | The execution is starting.                               |
| "running"        | The execution is running.                                |
| "awaiting_input" | The execution is suspended and awaiting input to resume. |
| "succeeded"      | The execution has succeeded.                             |
| "failed"         | The execution failed for some reason.                    |
| "cancelled"      | The execution has been cancelled by the user.            |

Every time an execution enters a new state, a `Transition` object is created on the backend with details of the state change. You can retrieve the transition history of the execution.

## Memory (Upcoming)