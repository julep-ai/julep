import os
import uuid
import yaml
from julep import Client

# Global UUID is generated for agent and task
AGENT_UUID = uuid.uuid4()
TASK_UUID = uuid.uuid4()

# Create Julep Client with the API Key
api_key = os.getenv("JULEP_API_KEY")
if not api_key:
    raise ValueError("JULEP_API_KEY not found in environment variables")

client = Client(api_key=api_key, environment="dev")

# Define agent properties
name = "Sarcastic News Bot"
about = "An AI agent specialized in generating sarcastic news headlines."
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
    model="gpt-4o",
)

# Define the task
task_def = yaml.safe_load("""
name: Sarcasm Headline Generator

tools:
- name: brave_search
  type: integration
  integration:
    provider: brave
    setup:
      api_key: "YOUR_BRAVE_API_KEY"

main:
- tool: brave_search
  arguments:
    query: "_.topic + ' funny'"

- prompt:
  - role: system
    content: >-
      You are a sarcastic news headline writer. Generate a witty and sarcastic headline
      for the topic {{inputs[0].topic}}. Use the following information for context: {{_}}
  unwrap: true
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
        "topic": "elon musk"
    }
)

# Waiting for the execution to complete
import time 
time.sleep(5)

# Getting the execution details
execution = client.executions.get(execution.id)
print("Execution output:", execution.output)

# Listing all the steps of a defined task
transitions = client.executions.transitions.list(execution_id=execution.id).items
print("Execution Steps:")
for transition in transitions:
    print(transition)

# Stream the steps of the defined task
print("Streaming execution transitions:")
print(client.executions.transitions.stream(execution_id=execution.id))

