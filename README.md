<!--
****************
** Guidelines **
****************

**Chosen Approach:**

The **Quick Start Guide Focused README** is the most promising for optimizing the time to first workflow. It allows developers to get hands-on experience quickly, which is essential for engagement and understanding.

* * *

**Outline for the README:**

1.  **Title and Badges**
    *   Julep Logo or Title
    *   Build status, npm version, license badges
2.  **Introduction**
    *   _Briefly explain what Julep is and its purpose._
    *   Emphasize how it simplifies building persistent AI agents with workflows.
3.  **Features**
    *   _Highlight key features with a focus on "tasks" (AI workflows)._
    *   Mention support for persistent sessions, tool integration, and document management.
4.  **Installation**
    *   _Provide npm installation command:_
        
        bash
        
        Copy code
        
        `npm install julep`
        
5.  **Quick Start Guide**
    *   **Step 1: Import Julep**
        *   _Show how to import Julep into a project._
            
            javascript
            
            Copy code
            
            `const Julep = require('julep');`
            
    *   **Step 2: Initialize the Agent**
        *   _Guide on creating a new agent with basic settings._
            
            javascript
            
            Copy code
            
            `const agent = new Julep.Agent({  name: 'MyAgent',  model: 'gpt-4-turbo', });`
            
    *   **Step 3: Chat with the Agent**
        *   _Provide a simple example of a chat with the agent._
            
            javascript
            
            Copy code
            
            `const response = await client.sessions.chat({  session_id: session.id,  message: 'Hello, how are you?' });`   
            
    *   **Step 4: Define a Task (Workflow)**
        *   _Provide a simple example of a task definition._
            
            javascript
            
            Copy code
            
            `const task = {  name: 'GreetingTask',  main: [    {      prompt: 'Say hello to the user.',    },  ], }; agent.addTask(task);`
            
    *   **Step 5: Execute the Task**
        *   _Show how to run the task and handle the output._
            
            javascript
            
            Copy code
            
            `agent.executeTask('GreetingTask').then((output) => {  console.log(output); });`
            
6.  **Understanding Tasks**
    *   _Explain what tasks are and how they function within Julep._
    *   Describe different types of workflow steps.
        *   Prompt, Tool Call, Evaluate, etc.
    *   _Note:_ Link to detailed documentation for each step type.
7.  **Advanced Features**
    *   _Briefly mention other capabilities:_
        *   Adding tools to agents.
        *   Managing sessions and users.
        *   Document integration and search.
8.  **API Reference**
    *   _Link to full API documentation._
    *   Mention key endpoints for agents, tasks, and executions.
9.  **Examples and Tutorials**
    *   _Provide links to example projects or further tutorials._
    *   Encourage users to explore and build upon provided examples.
10.  **Contributing**
    *   _Instructions for contributing to the project._
    *   Link to contribution guidelines and code of conduct.
11.  **Support and Community**
    *   _Information on how to get help._
    *   Links to community forums, chat groups, or issue trackers.
12.  **License**
    *   _State the project's license._
    *   Provide a link to the LICENSE file.
13.  **Acknowledgements**
    *   _Credit to contributors and used resources._

* * *

**Notes:**

*   **Code Examples:** Ensure all code snippets are easy to understand and copy-paste ready.
*   **Simplicity:** Keep explanations concise to maintain focus on getting started quickly.
*   **Links:** Include hyperlinks to detailed documentation sections for users who want to delve deeper.
*   **Visuals:** Consider adding diagrams or images to illustrate concepts if possible.
*   **Tone:** Maintain an encouraging and helpful tone throughout the README
-->

<sup>English | [中文翻译](/README-CN.md)</sup>

<div align="center">
    <img src="https://socialify.git.ci/julep-ai/julep/image?description=1&descriptionEditable=Rapidly%20build%20AI%20workflows%20and%20agents&font=Source%20Code%20Pro&logo=https%3A%2F%2Fraw.githubusercontent.com%2Fjulep-ai%2Fjulep%2Fdev%2F.github%2Fjulep-logo.svg&owner=1&pattern=Solid&stargazers=1&theme=Auto" alt="julep" width="640" height="320" />
</div>

<p align="center">
  <br />
  <a href="https://docs.julep.ai" rel="dofollow"><strong>Explore Docs</strong></a>
  ·
  <a href="https://discord.com/invite/JTSBGRZrzj" rel="dofollow">Discord</a>
  ·
  <a href="https://x.com/julep_ai" rel="dofollow">𝕏</a>
  ·
  <a href="https://www.linkedin.com/company/julep-ai" rel="dofollow">LinkedIn</a>
</p>


<p align="center">
    <a href="https://www.npmjs.com/package/@julep/sdk"><img src="https://img.shields.io/npm/v/%40julep%2Fsdk?style=social&amp;logo=npm&amp;link=https%3A%2F%2Fwww.npmjs.com%2Fpackage%2F%40julep%2Fsdk" alt="NPM Version"></a>
    <span>&nbsp;</span>
    <a href="https://pypi.org/project/julep"><img src="https://img.shields.io/pypi/v/julep?style=social&amp;logo=python&amp;label=PyPI&amp;link=https%3A%2F%2Fpypi.org%2Fproject%2Fjulep" alt="PyPI - Version"></a>
    <span>&nbsp;</span>
    <a href="https://hub.docker.com/u/julepai"><img src="https://img.shields.io/docker/v/julepai/agents-api?sort=semver&amp;style=social&amp;logo=docker&amp;link=https%3A%2F%2Fhub.docker.com%2Fu%2Fjulepai" alt="Docker Image Version"></a>
    <span>&nbsp;</span>
    <a href="https://choosealicense.com/licenses/apache/"><img src="https://img.shields.io/github/license/julep-ai/julep" alt="GitHub License"></a>
</p>

*****

## 🎉🚀 **Exciting News: Julep 1.0 Alpha Release!** 🚀🎉

We're thrilled to announce the **alpha** release of <u>Julep 1.0</u>! 🥳

🌟 **What's New:**
- Enhanced workflow capabilities
- Improved agent persistence
- Tons of in-built tool integrations (like dalle, google search, sendgrid, etc.)
- Streamlined API

🧪 Try it out and help shape the future of AI workflows!

> [!NOTE]
> While we are in beta, you can reach out on [Discord](https://discord.com/invite/JTSBGRZrzj) to get your API key.

> [!TIP]
> 🐛 Found a bug? Have a suggestion? We'd love to hear from you!
>   Join our [Discord](https://discord.com/invite/JTSBGRZrzj) or open an [issue](https://github.com/julep-ai/julep/issues).

Stay tuned for more updates as we approach our stable release! 📢


## Introduction

Julep is an open-source platform for creating persistent AI agents with customizable workflows. It provides tools to develop, manage, and deploy AI-driven applications, focusing on flexibility and ease of use.

With Julep, you can:
- Quickly develop AI agents that retain context and state across interactions
- Design and execute sophisticated workflows tailored to your AI agents
- Seamlessly integrate various tools and APIs into your AI workflows
- Effortlessly manage persistent sessions and user interactions

Whether you're developing a chatbot, automating tasks, or building a complex AI assistant, Julep provides the flexibility and features you need to turn your ideas into reality swiftly and efficiently.

<!-- TODO: Add a screencast -->

<details>
<summary>Here's a quick python example:</summary>

<!-- TODO: Add a gif that shows the execution of the task in the README -->

<pre><code class="language-python">
from julep import Julep, AsyncJulep

# 🔑 Initialize the Julep client
#     Or alternatively, use AsyncJulep for async operations
client = Julep(api_key="your_api_key")

##################
## 🤖 Agent 🤖 ##
##################

# Create a research agent
agent = client.agents.create(
    name="Research Agent",
    model="claude-3.5-sonnet",
    about="You are a research agent designed to handle research inquiries.",
)

# 🔍 Add a web search tool to the agent
client.agents.tools.create(
    agent_id=agent.id,
    name="web_search",  # Should be python valid variable name
    description="Use this tool to research inquiries.",
    integration={
        "provider": "brave",
        "method": "search",
        "setup": {
            "api_key": "your_brave_api_key",
        },
    },
)

#################
## 💬 Chat 💬 ##
#################

# Start an interactive chat session with the agent
session = client.sessions.create(
    agent_id=agent.id,
    context_overflow="adaptive",  # 🧠 Julep will dynamically compute the context window if needed
)

# 🔄 Chat loop
while (user_input := input("You: ")) != "exit":
    response = client.sessions.chat(
        session_id=session.id,
        message=user_input,
    )

    print("Agent: ", response.choices[0].message.content)


#################
## 📋 Task 📋 ##
#################

# Create a recurring research task for the agent
task = client.tasks.create(
    agent_id=agent.id,
    name="Research Task",
    description="Research the given topic every 24 hours.",
    #
    # 🛠️ Task specific tools
    tools=[
        {
            "name": "send_email",
            "description": "Send an email to the user with the results.",
            "api_call": {
                "method": "post",
                "url": "https://api.sendgrid.com/v3/mail/send",
                "headers": {"Authorization": "Bearer YOUR_SENDGRID_API_KEY"},
            },
        }
    ],
    #
    # 🔢 Task main steps
    main=[
        #
        # Step 1: Research the topic
        {
            # `_` (underscore) variable refers to the previous step's output
            # Here, it points to the topic input from the user
            "prompt": "Look up topic '{{_.topic}}' and summarize the results.",
            "tools": [{"ref": {"name": "web_search"}}],  # 🔍 Use the web search tool from the agent
            "unwrap": True,
        },
        #
        # Step 2: Send email with research results
        {
            "tool": "send_email",
            "arguments": {
                "subject": "Research Results",
                "body": "'Here are the research results for today: ' + _.content",
                "to": "inputs[0].email",  # Reference the email from the user's input
            },
        },
        #
        # Step 3: Wait for 24 hours before repeating
        {"sleep": "24 * 60 * 60"},
    ],
)

# 🚀 Start the recurring task
client.executions.create(task_id=task.id, input={"topic": "Python"})

# 🔁 This will run the task every 24 hours,
#    research for the topic "Python", and
#    send the results to the user's email
</code></pre>
</details>


## Features

Julep simplifies the process of building persistent AI agents with customizable workflows. Key features include:

- **Persistent AI Agents**: Create and manage AI agents that maintain context across interactions.
- **Customizable Workflows**: Design complex, multi-step AI workflows using Tasks.
- **Tool Integration**: Seamlessly integrate various tools and APIs into your AI workflows.
- **Document Management**: Efficiently manage and search through documents for your agents.
- **Session Management**: Handle persistent sessions for continuous interactions.
- **Flexible Execution**: Support for parallel processing, conditional logic, and error handling in workflows.

## Installation

To get started with Julep, install it using [npm](https://www.npmjs.com/package/@julep/sdk) or [pip](https://pypi.org/project/julep/):

```bash
npm install @julep/sdk
```

or

```bash
pip install julep
```

> [!TIP]
> ~~Get your API key [here](https://app.julep.ai/api-keys).~~
>  
> While we are in beta, you can reach out on [Discord](https://discord.com/invite/JTSBGRZrzj) to get your API key.

## Quick Start Guide

### Step 1: Import Julep

First, import the Julep SDK into your project:

```javascript
const Julep = require('@julep/sdk');
```

or

```python
from julep import AsyncJulep
```

### Step 2: Initialize the Agent

Create a new agent with basic settings:

```javascript
const julep = new Julep({ apiKey: 'your-api-key' });

const agent = await julep.agents.create({
  name: 'ResearchAssistant',
  model: 'gpt-4-turbo',
  about: "You are a creative storytelling agent that can craft engaging stories and generate comic panels based on ideas.",
});
```

or

```python
client = AsyncJulep(api_key="your_api_key")

agent = await client.agents.create(
    name="Storytelling Agent",
    model="gpt-4-turbo",
    about="You are a creative storytelling agent that can craft engaging stories and generate comic panels based on ideas.",
)
```

### Step 3: Chat with the Agent

Start an interactive chat session with the agent:

```javascript
const session = await julep.sessions.create({
  agentId: agent.id,
}); 

// Send messages to the agent
const response = await julep.sessions.chat({
  sessionId: session.id,
  message: 'Hello, can you tell me a story?',
});

console.log(response);
```

or

```python
session = await client.sessions.create(agent_id=agent.id)

# Send messages to the agent
response = await client.sessions.chat(
    session_id=session.id,
    message="Hello, can you tell me a story?",
)

print(response)
``` 


### Step 4: Create a multi-step Task

Let's define a multi-step task to create a story and generate a paneled comic strip based on an input idea:

```python
# 🛠️ Add an image generation tool (DALL·E) to the agent
await client.agents.tools.create(
    agent_id=agent.id,
    name="image_generator",
    description="Use this tool to generate images based on descriptions.",
    integration={
        "provider": "dalle",
        "method": "generate_image",
        "setup": {
            "api_key": "your_dalle_api_key",
        },
    },
)

# 📋 Task
# Create a task that takes an idea and creates a story and a 4-panel comic strip
task = await client.tasks.create(
    agent_id=agent.id,
    name="Story and Comic Creator",
    description="Create a story based on an idea and generate a 4-panel comic strip illustrating the story.",
    main=[
        # Step 1: Generate a story and outline into 4 panels
        {
            "prompt": [
                {
                    "role": "system",
                    "content": "You are {{agent.name}}. {{agent.about}}"
                },
                {
                    "role": "user",
                    "content": (
                        "Based on the idea '{{_.idea}}', write a short story suitable for a 4-panel comic strip. "
                        "Provide the story and a numbered list of 4 brief descriptions for each panel illustrating key moments in the story."
                    ),
                },
            ],
            "unwrap": True,
        },
        # Step 2: Extract the panel descriptions and story
        {
            "evaluate": {
                "story": "_.split('1. ')[0].strip()",
                "panels": "re.findall(r'\\d+\\.\\s*(.*?)(?=\\d+\\.\\s*|$)', _)",
            }
        },
        # Step 3: Generate images for each panel using the image generator tool
        {
            "foreach": {
                "in": "_.panels",
                "do": {
                    "tool": "image_generator",
                    "arguments": {
                        "description": "_",
                    },
                },
            },
        },
        # Step 4: Generate a catchy title for the story
        {
            "prompt": [
                {
                    "role": "system",
                    "content": "You are {{agent.name}}. {{agent.about}}"
                },
                {
                    "role": "user",
                    "content": "Based on the story below, generate a catchy title.\n\nStory: {{outputs[1].story}}",
                },
            ],
            "unwrap": True,
        },
        # Step 5: Return the story, the generated images, and the title
        {
            "return": {
                "title": "outputs[3]",
                "story": "outputs[1].story",
                "comic_panels": "[output.image.url for output in outputs[2]]",
            }
        },
    ],
)
```

> [!TIP]
> node.js version of this is similar.

### Step 5: Execute the Task

```python
# 🚀 Execute the task with an input idea
execution = await client.executions.create(
    task_id=task.id,
    input={"idea": "A cat who learns to fly"}
)

# 🎉 Watch as the story and comic panels are generated
await client.executions.stream(execution_id=execution.id)
```

This example demonstrates how to create an agent with a custom tool, define a complex task with multiple steps, and execute it to generate a creative output.

<!-- TODO: Add gif that shows the execution of the task in the README -->

> [!TIP]
> You can find another node.js example [here](example.ts) or python example [here](example.py).

## Concepts

Julep is built on several key technical components that work together to create powerful AI workflows:

### Agents
AI-powered entities backed by large language models (LLMs) that execute tasks and interact with users. Agents are the core functional units of Julep.

```mermaid
graph TD
    Agent[Agent] --> LLM[Large Language Model]
    Agent --> Tasks[Tasks]
    Agent --> Users[Users]
    Tasks --> Tools[Tools]
```

### Users
Entities that interact with agents. Users can be associated with sessions and have their own metadata, allowing for personalized interactions.

```mermaid
graph LR
    User[User] --> Sessions[Sessions]
    Sessions --> Agents[Agents]
    Sessions --> Metadata[Metadata]
```

### Sessions
Stateful interactions between agents and users. Sessions maintain context across multiple exchanges and can be configured for different behaviors, including context management and overflow handling.

```mermaid
graph LR
    Sessions[Sessions] --> Agents[Agents]
    Sessions --> Users[Users]
    Sessions --> ContextManagement[Context Management]
    Sessions --> OverflowHandling[Overflow Handling]
```

### Tasks
Multi-step, programmatic workflows that agents can execute. Tasks define complex operations and can include various types of steps, such as prompts, tool calls, and conditional logic.

```mermaid
graph TD
    Tasks[Tasks] --> Steps[Workflow Steps]
    Steps --> Prompt[Prompt]
    Steps --> ToolCalls[Tool Calls]
    Steps --> ConditionalLogic[Conditional Logic]
```

### Tools
Integrations that extend an agent's capabilities. Tools can be user-defined functions, system tools, or third-party API integrations. They allow agents to perform actions beyond text generation.

```mermaid
graph LR
    Tools[Tools] --> UserDefinedFunctions[User-Defined Functions]
    Tools --> SystemTools[System Tools]
    Tools --> ThirdPartyAPIs[Third-Party APIs]
```

### Documents
Text or data objects that can be associated with agents or users. Documents are vectorized and stored in a vector database, enabling semantic search and retrieval during agent interactions.

```mermaid
graph LR
    Documents[Documents] --> VectorDatabase[Vector Database]
    Documents --> SemanticSearch[Semantic Search]
    Documents --> AgentsOrUsers[Agents or Users]
```

### Executions
Instances of tasks that have been initiated with specific inputs. Executions have their own lifecycle and state machine, allowing for monitoring, management, and resumption of long-running processes.

```mermaid
graph LR
    Executions[Executions] --> Tasks[Tasks]
    Executions --> Lifecycle[Lifecycle]
    Executions --> Monitoring[Monitoring]
    Executions --> Management[Management]
    Executions --> Resumption[Resumption]
```

For a more detailed explanation of these concepts and their interactions, please refer to our [Concepts Documentation](https://github.com/julep-ai/julep/blob/dev/docs/julep-concepts.md).

## Understanding Tasks

Tasks are the core of Julep's workflow system. They allow you to define complex, multi-step AI workflows that your agents can execute. Here's a brief overview of task components:

- **Name and Description**: Each task has a unique name and description for easy identification.
- **Main Steps**: The core of a task, defining the sequence of actions to be performed.
- **Tools**: Optional integrations that extend the capabilities of your agent during task execution.

### Types of Workflow Steps

Tasks in Julep can include various types of steps:

1. **Prompt**: Send a message to the AI model and receive a response.
   ```python
   {"prompt": "Analyze the following data: {{data}}"}
   ```

2. **Tool Call**: Execute an integrated tool or API.
   ```python
   {"tool": "web_search", "arguments": {"query": "Latest AI developments"}}
   ```

3. **Evaluate**: Perform calculations or manipulate data.
   ```python
   {"evaluate": {"average_score": "sum(scores) / len(scores)"}}
   ```

4. **Conditional Logic**: Execute steps based on conditions.
   ```python
   {"if": "score > 0.8", "then": [...], "else": [...]}
   ```

5. **Loops**: Iterate over data or repeat steps.
   ```python
   {"foreach": {"in": "data_list", "do": [...]}}
   ```

| Step Name          | Description                                                                                      | Input                                                |
|--------------------|--------------------------------------------------------------------------------------------------|------------------------------------------------------|
| **Prompt**         | Send a message to the AI model and receive a response.                                           | Prompt text or template                              |
| **Tool Call**      | Execute an integrated tool or API.                                                               | Tool name and arguments                              |
| **Evaluate**       | Perform calculations or manipulate data.                                                         | Expressions or variables to evaluate                |
| **Wait for Input** | Pause workflow until input is received.                                                          | Any required user or system input                    |
| **Log**            | Log a specified value or message.                                                                | Message or value to log                              |
| **Embed**          | Embed text into a specific format or system.                                                    | Text or content to embed                             |
| **Search**         | Perform a document search based on a query.                                                     | Search query                                         |
| **Get**            | Retrieve a value from a key-value store.                                                        | Key identifier                                       |
| **Set**            | Assign a value to a key in a key-value store.                                                   | Key and value to assign                              |
| **Parallel**       | Run multiple steps in parallel.                                                                  | List of steps to execute simultaneously              |
| **Foreach**        | Iterate over a collection and perform steps for each item.                                      | Collection or list to iterate over                   |
| **MapReduce**      | Map over a collection and reduce the results based on an expression.                            | Collection to map and reduce expressions             |
| **If Else**        | Conditional execution of steps based on a condition.                                           | Condition to evaluate                                |
| **Switch**         | Execute steps based on multiple conditions, similar to a switch-case statement.                  | Multiple conditions and corresponding steps          |
| **Yield**          | Run a subworkflow and await its completion.                                                     | Subworkflow identifier and input data                |
| **Error**          | Handle errors by specifying an error message.                                                   | Error message or handling instructions               |
| **Sleep**          | Pause the workflow for a specified duration.                                                    | Duration (seconds, minutes, etc.)                    |
| **Return**         | Return a value from the workflow.                                                                | Value to return                                       |

For detailed information on each step type and advanced usage, please refer to our [Task Documentation](https://docs.julep.ai/tasks).

## Advanced Features

Julep offers a range of advanced features to enhance your AI workflows:

### Adding Tools to Agents

Extend your agent's capabilities by integrating external tools and APIs:

```python
client.agents.tools.create(
    agent_id=agent.id,
    name="web_search",
    description="Search the web for information.",
    integration={
        "provider": "google",
        "method": "search",
        "setup": {"api_key": "your_google_api_key"},
    },
)
```

### Managing Sessions and Users

Julep provides robust session management for persistent interactions:

```python
session = client.sessions.create(
    agent_id=agent.id,
    user_id="user123",
    context_overflow="adaptive"
)

# Continue conversation in the same session
response = client.sessions.chat(
    session_id=session.id,
    message="Follow up on our previous conversation."
)
```

### Document Integration and Search

Easily manage and search through documents for your agents:

```python
# Upload a document
document = client.documents.create(
    file="path/to/document.pdf",
    metadata={"category": "research_paper"}
)

# Search documents
results = client.documents.search(
    query="AI advancements",
    filter={"category": "research_paper"}
)
```

For more advanced features and detailed usage, please refer to our [Advanced Features Documentation](https://docs.julep.ai/advanced-features).

## SDK Reference

- [Node.js SDK](https://github.com/julep-ai/node-sdk/blob/main/api.md)
- [Python SDK](https://github.com/julep-ai/python-sdk/blob/main/api.md)

## API Reference

Explore our comprehensive API documentation to learn more about agents, tasks, and executions:

- [Agents API](https://api.julep.ai/api/docs#tag/agents)
- [Tasks API](https://api.julep.ai/api/docs#tag/tasks)
- [Executions API](https://api.julep.ai/api/docs#tag/executions)

## Examples and Tutorials

Discover example projects and tutorials to help you get started and build upon provided examples:

- [Example Projects](https://github.com/julep-ai/julep/tree/main/examples)
- [Tutorials](https://docs.julep.ai/tutorials)

## Contributing

We welcome contributions to the project! Learn how to contribute and our code of conduct:

- [Contributing Guidelines](https://github.com/julep-ai/julep/blob/main/CONTRIBUTING.md)
- [Code of Conduct](https://github.com/julep-ai/julep/blob/main/CODE_OF_CONDUCT.md)

## Support and Community

Join our community to get help, ask questions, and share your ideas:

- [Discord](https://discord.com/invite/JTSBGRZrzj)
- [GitHub Discussions](https://github.com/julep-ai/julep/discussions)
- [Twitter](https://twitter.com/julep_ai)

## License

This project is licensed under the [Apache License 2.0](https://github.com/julep-ai/julep/blob/main/LICENSE).

## Acknowledgements

We would like to express our gratitude to all contributors and the open-source community for their valuable resources and contributions.