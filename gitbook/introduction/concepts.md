# Concepts

## Agent components

### Agents

At the heart of Julep AI are the _Agents_—autonomous applications designed to perform tasks using advanced language models. Each agent possesses a unique identity, defined by characteristics such as name, description, metadata, and a set of instructions. They function by planning actions, choosing tools, and executing steps towards achieving specific goals.

### Memories and Scoping

Agents in Julep AI have a nuanced memory system, storing and recalling _Memories_ in three categories: episodic (events), implicit (beliefs), or semantic (facts and information). They are akin to a human's recollection of past experiences and acquired knowledge and their design was influenced by ideas from contemporary cognitive science.

Memories allow agents to continuously learn from user engagements and task executions. They enhance its ability to adapt and respond effectively over time, significantly personalizing the user experience.

Memories are specific to a given user, allowing agents to provide personalized interactions and retain crucial context from previous engagements but also maintaining privacy and granular control.

### Sessions

_Sessions_ are interactive scenarios where a user engages with an agent in a conversational format, with the agent responding in real-time. A user can basically "talk" to an agent inside a session where the responses are expected to be immediately returned. The agent can access memories, follow sophisticated prompts and run _Instant Tools_ (tools that have predictable latency and can be executed mid-inference).

For longer and more complex actions, you can use _Tasks_ which allow for long-running operations and have access to more powerful tools like _API Calls_, a _Web Bowser_, etc at the expense of being run asynchronously. Sessions can invoke tasks by the same agent autonomously but don't wait for completion of the task.

### Tasks, Scheduling and Runs

Tasks are more complex operations that may run over an extended period, involving multiple steps and tools. While sessions are for immediate interaction, tasks are structured to handle long-term objectives, acting as automated workflows.

Every task is essentially a State Machine definition where the LLM dynamically decides the transitions of the states. In order to invoke a task, one can either use the API or by creating a _Scheduled Task_ which defines a fixed timestamp, timer or an interval that automatically invokes the task. The agents can initiate tasks at predetermined times or intervals, ensuring timely execution of operations without manual intervention.

Each execution of a session or task is a Run, with its own unique run\_id. Runs track the progress of agents' actions, managing transitions and maintaining state, critical for monitoring and continuity.

***

## Platform

**Platform** Julep AI's platform is a composite system that includes a Web-based IDE for developing agents, an execution platform for running agents over extended periods, and an API SDK for integrating these agents into existing product ecosystems. This triad enables product teams to collaboratively build, test, and deploy sophisticated AI agents with efficiency and scale.

**Prototyping** Prototyping within Julep AI is the rapid creation and iteration of AI agents. It involves defining the agent's capabilities, experimenting with various prompting strategies, and refining their functionality through a Prompt IDE. This IDE is a central feature of the platform, offering developers and non-developers alike the ability to visually compose, test, and adjust prompts in real-time, ensuring immediate and visual feedback on the agent's performance and behavior.

**Shipping** "Shipping" refers to the process of transitioning an AI agent from prototype to a deployed, operational state. It encompasses handing off the agent to a development team for integration into products or services, with support for production features like monitoring, service integration, and code export. This phase is critical for moving from a test environment to real-world application, where the agent can interact with users and systems in a live setting.
