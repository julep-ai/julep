import uuid
import yaml
from julep import Client

# Global UUID is generated for agent and task
AGENT_UUID = uuid.uuid4()
TASK_UUID = uuid.uuid4()

# Creating Julep Client with the API Key
api_key = ""  # Your API key here
client = Client(api_key=api_key, environment="dev")

# Creating an "agent"
name = "Multi-Step Task Agent"
about = "An agent capable of executing complex multi-step tasks."
default_settings = {
    "temperature": 0.7,
    "top_p": 1,
    "min_p": 0.01,
    "presence_penalty": 0,
    "frequency_penalty": 0,
    "length_penalty": 1.0,
    "max_tokens": 150,
}

# Create the agent
agent = client.agents.create_or_update(
    agent_id=AGENT_UUID,
    name=name,
    about=about,
    model="gpt-4-turbo",
)

# Add a web search tool to the agent
client.agents.tools.create(
    agent_id=AGENT_UUID,
    name="web_search",
    description="Search the web for information.",
    integration={
        "provider": "brave",
        "method": "search",
        "setup": {"api_key": "your_brave_api_key"},
    },
)

# Defining a Task with various step types
task_def = yaml.safe_load("""
name: Multi-Step Task Demonstration

input_schema:
  type: object
  properties:
    topic:
      type: string
      description: The topic to research and summarize.

tools:
- name: web_search
  type: integration
  integration:
    provider: brave
    setup:
      api_key: "your_api_key"

main:
# Step 1: Prompt - Initial research question
- prompt:
  - role: system
    content: "You are a research assistant. Your task is to formulate three specific research questions about the given topic: {{inputs[0].topic}}"
  unwrap: true

# Step 2: Tool Call - Web search for each question
- foreach:
    in: "_.split('\n')"
    do:
      tool: web_search
      arguments:
        query: _

# Step 3: Evaluate - Extract relevant information
- evaluate:
    relevant_info: "[output for output in _]"

# Step 4: Conditional Logic - Check if enough information is gathered
- if: "len(_.relevant_info) >= 3"
  then:
      prompt:
      - role: system
        content: "Summarize the following information about {{inputs[0].topic}}:\n{{_.relevant_info}}"
      unwrap: true
  else:
      prompt:
      - role: system
        content: "Not enough information gathered. Please provide a brief overview of {{inputs[0].topic}} based on your knowledge."
      unwrap: true

# Step 5: Log - Record the summary
- log: "Summary for {{inputs[0].topic}}: {{_}}"

# Step 6: Return - Final output
- return: 
    summary: "_"
    topic: "inputs[0].topic"
                          
""")

# Creating/Updating a task
task = client.tasks.create_or_update(
    task_id=TASK_UUID,
    agent_id=AGENT_UUID,
    **task_def
)

# Creating an Execution
execution = client.executions.create(
    task_id=TASK_UUID,
    input={
        "topic": "Artificial Intelligence in Healthcare"
    }
)

print(f"Execution ID: {execution.id}")

# Getting the execution details
execution = client.executions.get(execution.id)
print("Execution Output:")
print(execution.output)

# Listing all the steps of a defined task
transitions = client.executions.transitions.list(execution_id=execution.id).items
print("Execution Steps:")
for transition in transitions:
    print(transition)

# Streaming the execution steps
print("Streaming Execution Steps:")
for transition in client.executions.transitions.stream(execution_id=execution.id):
    print(transition)